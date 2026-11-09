import contextlib
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import os
import subprocess
import tempfile
import pty
import select
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stack_forge.cli.api import ApiClient, ApiError
from stack_forge.cli.connection import choose_connection


class ApiTest(unittest.TestCase):
    def setUp(self):
        """Запустить локальный HTTP-сервер для проверки CLI"""
        self.records = []
        self.connect_status = 200
        self.bad_ack = False
        self.bad_catalog = False
        self.reset_status = 200
        self.reset_reply = None
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                """Подавить стандартный HTTP-лог тестового сервера"""
                pass

            def respond(self, code, payload):
                """Отправить JSON-ответ тестового HTTP-сервера"""
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def do_GET(self):
                """Обработать GET-запрос тестового клиента"""
                owner.records.append(("GET", self.path, None, None))
                self.respond(
                    200,
                    {"bad": True}
                    if owner.bad_catalog
                    else [
                        {"id": "git", "title": "Git", "position": 1},
                    ],
                )

            def do_POST(self):
                """Обработать POST-запрос тестового клиента"""
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                owner.records.append(
                    ("POST", self.path, body, self.headers.get("Authorization"))
                )
                if self.path == "/api/v1/cli/connect":
                    self.respond(
                        owner.connect_status,
                        {
                            "session_id": "c7e1af73-5110-4c3d-9190-f8a3ef34d4ef",
                            "generation": 2,
                            "key": "test-secret-key",
                        },
                    )
                elif self.path in {"/api/v1/cli/heartbeat", "/api/v1/cli/disconnect"}:
                    self.respond(
                        200,
                        {
                            "session_id": body["session_id"],
                            "generation": body["generation"],
                            "connected": self.path.endswith("heartbeat"),
                        },
                    )
                else:
                    self.respond(
                        200,
                        {
                            "session_id": body["session_id"],
                            "generation": body["generation"],
                            "version": 99 if owner.bad_ack else body["version"],
                        },
                    )

            def do_DELETE(self):
                """Принять сброс сессии и вернуть управляемое подтверждение"""
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                owner.records.append(
                    ("DELETE", self.path, body, self.headers.get("Authorization"))
                )
                self.respond(
                    owner.reset_status,
                    (
                        {"reset_id": body["reset_id"], **owner.reset_reply}
                        if isinstance(owner.reset_reply, dict)
                        else owner.reset_reply
                    )
                    if owner.reset_reply is not None
                    else {
                        "session_id": body["session_id"],
                        "generation": body["generation"] + 1,
                        "reset_id": body["reset_id"],
                        "reset": True,
                    },
                )

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = ApiClient(
            f"http://127.0.0.1:{self.server.server_port}", timeout=0.3
        )

    def tearDown(self):
        """Остановить тестовый HTTP-сервер и освободить его ресурсы"""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run_command(self, *args, input_text="1\n", offline="0"):
        """Выполнить команду CLI отдельным процессом против тестового сервера"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-m", "stack_forge", *args],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
                cwd=directory,
                env=dict(
                    os.environ,
                    PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"),
                    STACK_FORGE_SERVER_URL=self.client.server_url,
                    STACK_FORGE_OFFLINE=offline,
                    STACK_FORGE_CONTROL_SOCKET="",
                ),
            )
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertNotIn("test-secret-key", result.stdout + result.stderr)
        return result

    def test_reset_command_uses_delete_and_exits_without_shell(self):
        """Проверить DELETE с ключом и данными сессии без запуска оболочки"""
        result = self.run_command("reset")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("История практики очищена", result.stdout)
        self.assertIn("Хорошего дня", result.stdout)
        self.assertNotIn("Папка проекта", result.stdout)
        self.assertEqual(
            [(method, path) for method, path, *_ in self.records],
            [
                ("GET", "/api/v1/catalog"),
                ("POST", "/api/v1/cli/connect"),
                ("DELETE", "/api/v1/cli/reset-practice"),
            ],
        )
        self.assertEqual(
            {
                key: value
                for key, value in self.records[-1][2].items()
                if key != "reset_id"
            },
            {"session_id": "c7e1af73-5110-4c3d-9190-f8a3ef34d4ef", "generation": 2},
        )
        self.assertEqual(self.records[-1][3], "Bearer test-secret-key")

    def test_reset_rejects_invalid_confirmation(self):
        """Отклонить неподтверждённый сброс и чужую сессию или поколение"""
        valid = {
            "session_id": "c7e1af73-5110-4c3d-9190-f8a3ef34d4ef",
            "generation": 3,
            "reset": True,
        }
        for reply in (
            [],
            {**valid, "reset": False},
            {**valid, "reset": 1},
            {**valid, "session_id": "other"},
            {**valid, "generation": 4},
            {**valid, "generation": "2"},
        ):
            with self.subTest(reply=reply):
                self.reset_reply = reply
                result = self.run_command("reset")
                self.assertEqual(result.returncode, 1)
                self.assertIn("Сервер не подтвердил сброс истории", result.stderr)
                self.assertNotIn("История практики очищена", result.stdout)

    def test_reset_http_error_does_not_retry(self):
        """Не повторять сброс автоматически при ошибке сервера"""
        for status in (401, 409, 500):
            with self.subTest(status=status):
                self.records.clear()
                self.reset_status = status
                result = self.run_command("reset")
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("История практики очищена", result.stdout)
                self.assertEqual(sum(row[0] == "DELETE" for row in self.records), 1)

    def test_reset_cancel_does_not_connect_or_delete(self):
        """Отменить сброс при выборе локального режима или завершении ввода"""
        for text in ("0\n", ""):
            with self.subTest(input=text):
                self.records.clear()
                result = self.run_command("reset", input_text=text)
                self.assertEqual(result.returncode, 0)
                self.assertIn("Сброс отменён", result.stdout)
                self.assertTrue(all(row[0] == "GET" for row in self.records))

    def test_reset_offline_is_rejected_without_requests(self):
        """Отклонить сброс без сервера до выбора курса"""
        result = self.run_command("reset", offline="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("требуется подключение к серверу", result.stderr)
        self.assertEqual(self.records, [])

    def test_help_and_invalid_arguments_do_not_access_server(self):
        """Проверить справку без TTY и отклонение неизвестных аргументов"""
        for args in (("--help",), ("-h",), ("reset", "--help")):
            with self.subTest(args=args):
                result = self.run_command(*args)
                self.assertEqual(result.returncode, 0)
                self.assertIn("stack-forge reset", result.stdout)
                self.assertNotIn("STACK_FORGE_SERVER_URL", result.stdout)
                self.assertEqual(self.records, [])
        for args in (("unknown",), ("reset", "extra")):
            with self.subTest(args=args):
                result = self.run_command(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("stack-forge --help", result.stderr)
                self.assertEqual(self.records, [])

    def test_course_selection_and_initial_snapshot(self):
        """Проверить выбор курса и доставку начального снимка CLI"""
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            patch("builtins.input", side_effect=["1"]),
        ):
            connection = choose_connection(self.client)
        self.assertNotIn("test-secret-key", output.getvalue())
        self.assertNotIn("test-secret-key", repr(connection))
        self.assertEqual(connection.generation, 2)
        self.client.send_initial(
            connection, {"kind": "no_repository", "path": "/tmp/project"}
        )
        self.assertEqual(self.records[1][2], {"course_slug": "git"})
        sent = self.records[2]
        self.assertEqual(sent[3], "Bearer test-secret-key")
        self.assertNotIn("key", sent[2])
        self.assertEqual(sent[2]["version"], 1)
        self.assertEqual(sent[2]["generation"], 2)

    def run_cli_flow(self, continuous=False):
        """Пройти диалог запуска CLI в тестовом PTY"""
        master, slave = pty.openpty()
        with tempfile.TemporaryDirectory() as directory:
            env = dict(
                os.environ,
                PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"),
                STACK_FORGE_SERVER_URL=self.client.server_url,
                STACK_FORGE_STATE_DIR=str(Path(directory) / ".sync-cache"),
                NO_COLOR="1",
            )
            env.pop("STACK_FORGE_OFFLINE", None)
            process = subprocess.Popen(
                [sys.executable, "-m", "stack_forge"],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                env=env,
            )
            output = bytearray()

            def until(expected):
                """Дождаться ожидаемого вывода тестового CLI"""
                deadline = time.monotonic() + 8
                received = bytearray()
                while expected not in received and time.monotonic() < deadline:
                    if select.select([master], [], [], 0.1)[0]:
                        received.extend(os.read(master, 65536))
                output.extend(received)
                self.assertIn(expected, received)

            try:
                until("Номер курса".encode())
                os.write(master, b"1\n")
                until("Папка проекта".encode())
                self.assertEqual(self.records[-1][1], "/api/v1/cli/connect")
                os.write(master, directory.encode() + b"\n")
                until(b" > ")
                os.write(master, b"printf 'CLI-SPACING\\n'\n")
                until(b" > ")
                self.assertRegex(bytes(output), rb"CLI-SPACING\r*\n\r*\n")
                deadline = time.monotonic() + 5
                while (
                    not any(r[1] == "/api/v1/cli/send-snapshot" for r in self.records)
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.05)
                if continuous:
                    os.write(
                        master,
                        b"git init -b main && printf one > file && git add file && git -c user.name=Test -c user.email=test@example.invalid commit -m first\n",
                    )
                    until(b" > ")

                    def wait_state(predicate, endpoint="/api/v1/cli/send-snapshot"):
                        """Дождаться записи ожидаемого состояния локального снимка"""
                        deadline = time.monotonic() + 8
                        while time.monotonic() < deadline:
                            sent = [r[2] for r in self.records if r[1] == endpoint]
                            if sent and predicate(sent[-1]["state"]):
                                return sent[-1]
                            time.sleep(0.05)
                        self.fail("Изменение Git не отправлено")

                    committed = wait_state(lambda state: state.get("head") is not None)
                    self.assertGreater(committed["version"], 1)
                    os.write(master, b"git status --short\n")
                    until(b" > ")
                    time.sleep(0.8)
                    sent = [
                        r[2]
                        for r in self.records
                        if r[1] == "/api/v1/cli/send-snapshot"
                    ]
                    self.assertEqual(sent[-1]["version"], committed["version"])
                    Path(directory, "file").write_text("IDE edit")
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        local = json.loads(Path(directory, "state.json").read_text())
                        if any(
                            item["worktree"] == "M"
                            for item in local["state"].get("files", [])
                        ):
                            break
                        time.sleep(0.05)
                    else:
                        self.fail("Локальное изменение файла не обнаружено")
                    sent = [
                        r[2]
                        for r in self.records
                        if r[1] == "/api/v1/cli/send-snapshot"
                    ]
                    self.assertEqual(sent[-1]["version"], committed["version"])
                    os.write(master, b"pwd\n")
                    until(b" > ")
                    graph_requests = [
                        r[2]
                        for r in self.records
                        if r[1] == "/api/v1/cli/send-snapshot"
                    ]
                    self.assertEqual(
                        graph_requests[-1]["version"], committed["version"]
                    )
                os.write(master, b"exit\n")
                until("Хорошего дня".encode())
                self.assertEqual(process.wait(timeout=5), 0)
                self.assertTrue(
                    any(r[1] == "/api/v1/cli/send-snapshot" for r in self.records)
                )
                self.assertTrue(
                    any(r[1] == "/api/v1/cli/heartbeat" for r in self.records)
                )
                self.assertTrue(
                    any(r[1] == "/api/v1/cli/disconnect" for r in self.records)
                )
                self.assertNotIn(b"test-secret-key", output)
                for path in Path(directory).iterdir():
                    if path.is_file():
                        self.assertNotIn(b"test-secret-key", path.read_bytes())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                os.close(master)
                os.close(slave)

    @unittest.skipUnless(sys.platform == "darwin", "Терминальная версия для macOS")
    def test_cli_connects_before_folder_and_keeps_key_out_of_files(self):
        """Проверить подключение до выбора папки и отсутствие ключа в файлах"""
        self.run_cli_flow()

    @unittest.skipUnless(sys.platform == "darwin", "Терминальная версия для macOS")
    def test_initial_delivery_error_keeps_shell_working(self):
        """Проверить работу оболочки при ошибке начальной доставки"""
        self.bad_ack = True
        self.run_cli_flow()

    @unittest.skipUnless(sys.platform == "darwin", "Терминальная версия для macOS")
    def test_external_edits_do_not_enqueue_graph_snapshots(self):
        """Проверить отсутствие снимков графа при одних внешних правках файлов"""
        self.run_cli_flow(continuous=True)

    def test_missing_session_allows_local_mode(self):
        """Проверить локальную работу при отсутствии браузерной сессии"""
        self.connect_status = 404
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            patch("builtins.input", side_effect=["1", "0"]),
        ):
            self.assertIsNone(choose_connection(self.client))
        self.assertIn("Откройте выбранный курс", output.getvalue())

    def test_invalid_catalog_allows_local_mode(self):
        """Проверить локальную работу при некорректном каталоге сервера"""
        self.bad_catalog = True
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("builtins.input", return_value=""),
        ):
            self.assertIsNone(choose_connection(self.client))

    def test_failed_or_mismatched_snapshot_is_not_confirmed(self):
        """Проверить отклонение неуспешного или неверного подтверждения снимка"""
        connection = self.client.connect("git")
        self.bad_ack = True
        with self.assertRaises(ApiError):
            self.client.send_initial(
                connection, {"kind": "no_repository", "path": "/tmp"}
            )

    def test_closed_server_allows_local_mode(self):
        """Проверить локальную работу при недоступном сервере"""
        self.server.shutdown()
        self.server.server_close()
        with (
            contextlib.redirect_stdout(io.StringIO()),
            patch("builtins.input", return_value=""),
        ):
            self.assertIsNone(choose_connection(self.client))


if __name__ == "__main__":
    unittest.main()
