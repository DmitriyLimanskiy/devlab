"""HTTP-проверки CLI на локальном сервере, без записи ключей в проект."""
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from devlab.api import ApiClient, ApiError
from devlab.connection import choose_connection


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.records = []
        self.connect_status = 200
        self.bad_ack = False
        self.bad_catalog = False
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self, code, payload):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def do_GET(self):
                owner.records.append(('GET', self.path, None, None))
                self.respond(200, {'bad': True} if owner.bad_catalog else [
                    {'id': 'git', 'title': 'Git', 'position': 1},
                ])

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                owner.records.append(('POST', self.path, body, self.headers.get('Authorization')))
                if self.path == '/api/v1/cli-connect':
                    self.respond(owner.connect_status, {
                        'session_id': 'c7e1af73-5110-4c3d-9190-f8a3ef34d4ef',
                        'generation': 2, 'key': 'test-secret-key',
                    })
                else:
                    self.respond(200, {'session_id': body['session_id'],
                                      'generation': body['generation'],
                                      'version': 99 if owner.bad_ack else body['version']})

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = ApiClient(f'http://127.0.0.1:{self.server.server_port}', timeout=0.3)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_course_selection_and_initial_snapshot(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch('builtins.input', side_effect=['1']):
            connection = choose_connection(self.client)
        self.assertNotIn('test-secret-key', output.getvalue())
        self.assertNotIn('test-secret-key', repr(connection))
        self.assertEqual(connection.generation, 2)
        self.client.send_initial(connection, {'kind': 'no_repository', 'path': '/tmp/project'})
        self.assertEqual(self.records[1][2], {'course_slug': 'git'})
        sent = self.records[2]
        self.assertEqual(sent[3], 'Bearer test-secret-key')
        self.assertNotIn('key', sent[2])
        self.assertEqual(sent[2]['version'], 1)
        self.assertEqual(sent[2]['generation'], 2)

    def run_cli_flow(self, continuous=False):
        master, slave = pty.openpty()
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'),
                       DEVLAB_SERVER_URL=self.client.server_url, DEVLAB_STATE_DIR=str(Path(directory) / '.sync-cache'), NO_COLOR='1')
            env.pop('DEVLAB_OFFLINE', None)
            process = subprocess.Popen([sys.executable, '-m', 'devlab'], stdin=slave,
                                       stdout=slave, stderr=slave, env=env)
            output = bytearray()
            def until(expected):
                deadline = time.monotonic() + 8
                received = bytearray()
                while expected not in received and time.monotonic() < deadline:
                    if select.select([master], [], [], 0.1)[0]:
                        received.extend(os.read(master, 65536))
                output.extend(received)
                self.assertIn(expected, received)
            try:
                until('Номер курса'.encode())
                os.write(master, b'1\n')
                until('Папка проекта'.encode())
                self.assertEqual(self.records[-1][1], '/api/v1/cli-connect')
                os.write(master, directory.encode() + b'\n')
                until(b' > ')
                deadline = time.monotonic() + 5
                while not any(r[1] == '/api/v1/cli-send-snapshot' for r in self.records) and time.monotonic() < deadline:
                    time.sleep(0.05)
                if continuous:
                    os.write(master, b"git init -b main && printf one > file && git add file && git -c user.name=Test -c user.email=test@example.invalid commit -m first\n")
                    until(b' > ')
                    def wait_state(predicate):
                        deadline = time.monotonic() + 8
                        while time.monotonic() < deadline:
                            sent = [r[2] for r in self.records if r[1] == '/api/v1/cli-send-snapshot']
                            if sent and predicate(sent[-1]['state']):
                                return sent[-1]
                            time.sleep(0.05)
                        self.fail('Изменение Git не отправлено')
                    committed = wait_state(lambda state: state.get('head') is not None)
                    self.assertGreater(committed['version'], 1)
                    os.write(master, b'git status --short\n')
                    until(b' > ')
                    time.sleep(0.8)
                    sent = [r[2] for r in self.records if r[1] == '/api/v1/cli-send-snapshot']
                    self.assertEqual(sent[-1]['version'], committed['version'])
                    Path(directory, 'file').write_text('IDE edit')
                    modified = wait_state(lambda state: any(item['path'] == 'file' and item['worktree'] == 'M' for item in state.get('files', [])))
                    self.assertGreater(modified['version'], committed['version'])
                    self.assertFalse(any('.sync-cache' in item['path'] for item in modified['state']['files']))
                os.write(master, b'exit\n')
                until('Сессия DevLab завершена.'.encode())
                self.assertEqual(process.wait(timeout=5), 0)
                self.assertEqual(self.records[-1][1], '/api/v1/cli-send-snapshot')
                self.assertNotIn(b'test-secret-key', output)
                for path in Path(directory).iterdir():
                    if path.is_file():
                        self.assertNotIn(b'test-secret-key', path.read_bytes())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                os.close(master)
                os.close(slave)

    @unittest.skipUnless(sys.platform == 'darwin', 'Терминальная версия для macOS')
    def test_cli_connects_before_folder_and_keeps_key_out_of_files(self):
        self.run_cli_flow()

    @unittest.skipUnless(sys.platform == 'darwin', 'Терминальная версия для macOS')
    def test_initial_delivery_error_keeps_shell_working(self):
        self.bad_ack = True
        self.run_cli_flow()

    @unittest.skipUnless(sys.platform == 'darwin', 'Терминальная версия для macOS')
    def test_git_commands_and_external_edits_are_sent(self):
        self.run_cli_flow(continuous=True)

    def test_missing_session_allows_local_mode(self):
        self.connect_status = 404
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch('builtins.input', side_effect=['1', '0']):
            self.assertIsNone(choose_connection(self.client))
        self.assertIn('Откройте выбранный курс', output.getvalue())

    def test_invalid_catalog_allows_local_mode(self):
        self.bad_catalog = True
        with contextlib.redirect_stdout(io.StringIO()), patch('builtins.input', return_value=''):
            self.assertIsNone(choose_connection(self.client))

    def test_failed_or_mismatched_snapshot_is_not_confirmed(self):
        connection = self.client.connect('git')
        self.bad_ack = True
        with self.assertRaises(ApiError):
            self.client.send_initial(connection, {'kind': 'no_repository', 'path': '/tmp'})

    def test_closed_server_allows_local_mode(self):
        self.server.shutdown()
        self.server.server_close()
        with contextlib.redirect_stdout(io.StringIO()), patch('builtins.input', return_value=''):
            self.assertIsNone(choose_connection(self.client))


if __name__ == '__main__':
    unittest.main()
