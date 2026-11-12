import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stack_forge.features.git_practice.worktree import WorktreeSender
from stack_forge.shared.api import Connection


class Client:
    timeout = 0.05
    server_url = "http://127.0.0.1:8080"

    def __init__(self):
        """Подготовить состояние тестового клиента и сценарий сетевых ошибок"""
        self.calls = []
        self.failures = 0

    def connect(self, url, **kwargs):
        """Создать тестовое соединение с управляемыми подтверждениями"""
        owner = self

        class Socket:
            def send(self, data):
                """Передать тестовый запрос или пакет и записать результат отправки"""
                self.payload = json.loads(data)
                owner.calls.append((self.payload["version"], self.payload["state"]))
                if owner.failures:
                    owner.failures -= 1
                    raise OSError("Нет связи")

            def recv(self, timeout):
                """Вернуть подтверждение версии от тестового WebSocket"""
                return json.dumps(
                    {
                        "type": "ack",
                        "session_id": "session",
                        "generation": 1,
                        "version": self.payload["version"],
                    }
                )

            def close(self):
                """Закрыть тестовое соединение без дополнительных действий"""
                pass

        return Socket()


class WorktreeSenderTest(unittest.TestCase):
    def wait_for(self, predicate):
        """Дождаться выполнения условия в пределах тестового таймаута"""
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.01)
        self.fail("Нет оперативного состояния")

    def test_only_latest_files_are_sent_without_graph(self):
        """Проверить отправку только последних файлов без графа коммитов"""
        client = Client()
        sender = WorktreeSender(
            client,
            Connection("session", 1, "secret"),
            retry_delay=0.01,
            connector=client.connect,
            poll_interval=0.01,
        )
        for index in range(3):
            sender.publish(
                {
                    "kind": "repository",
                    "path": "/repo",
                    "files": [{"path": str(index)}],
                    "commits": ["big graph"],
                    "refs": ["refs"],
                }
            )
        sender.start()
        try:
            self.wait_for(lambda: len(client.calls) == 1)
            self.assertEqual(
                client.calls[0],
                (3, {"kind": "repository", "path": "/repo", "files": [{"path": "2"}]}),
            )
            sender.publish(
                {"kind": "repository", "path": "/repo", "files": [{"path": "2"}]}
            )
            self.assertEqual(sender.version, 3)
        finally:
            sender.close()

    def test_retry_and_resend_restore_server_memory_without_new_version(self):
        """Проверить восстановление памяти backend повтором прежней версии файлов"""
        client = Client()
        client.failures = 1
        sender = WorktreeSender(
            client,
            Connection("session", 1, "secret"),
            retry_delay=0.01,
            resend_interval=0.03,
            connector=client.connect,
            poll_interval=0.01,
        )
        sender.publish({"kind": "no_repository", "path": "/repo"})
        sender.start()
        try:
            self.wait_for(lambda: len(client.calls) >= 3)
            self.assertTrue(all(version == 1 for version, _ in client.calls))
        finally:
            sender.close()

    def test_polling_ignores_stale_and_partial_state_file(self):
        """Проверить игнорирование старого и недописанного state.json"""
        client = Client()
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "state.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "generator": "stack-forge-cli",
                        "updated_at": 1,
                        "state": {"kind": "no_repository", "path": "/old"},
                    }
                )
            )
            sender = WorktreeSender(
                client,
                Connection("session", 1, "secret"),
                snapshot=snapshot,
                connector=client.connect,
                poll_interval=0.01,
            )
            sender.poll_snapshot()
            self.assertIsNone(sender.latest)
            snapshot.write_text('{"state":')
            sender.poll_snapshot()
            self.assertIsNone(sender.latest)
            snapshot.write_text(
                json.dumps(
                    {
                        "generator": "stack-forge-cli",
                        "updated_at": time.time(),
                        "state": {"kind": "no_repository", "path": "/current"},
                    }
                )
            )
            sender.start()
            try:
                self.wait_for(lambda: len(client.calls) == 1)
                self.assertEqual(client.calls[0][1]["path"], "/current")
                sender.poll_snapshot()
                self.assertEqual(sender.version, 1)
            finally:
                sender.close()
