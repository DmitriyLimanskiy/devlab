"""Очередь, повторы и согласование подтверждений без терминальных блокировок."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from devlab.api import ApiError, Connection
from devlab.sync import SnapshotSender


class Client:
    server_url = 'http://127.0.0.1:8080'
    timeout = 0.1

    def __init__(self):
        self.calls = []
        self.failures = 0
        self.permanent = False
        self.entered = threading.Event()
        self.release = None

    def send_snapshot(self, connection, state, version):
        self.calls.append((version, state))
        self.entered.set()
        if self.release is not None:
            self.release.wait(2)
        if self.permanent:
            raise ApiError('Ключ недействителен', retryable=False)
        if self.failures:
            self.failures -= 1
            raise ApiError('Сеть недоступна')


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.client = Client()
        self.connection = Connection('c7e1af73-5110-4c3d-9190-f8a3ef34d4ef', 2, 'secret')
        self.sender = SnapshotSender(self.client, self.connection, self.temp.name,
                                     self.temp.name, retry_delay=0.03, max_delay=0.05)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.01)
        self.fail('Не дождались результата фонового отправителя')

    def start(self):
        self.sender.start()
        self.addCleanup(self.sender.close)

    def test_retry_uses_same_version_and_deduplicates(self):
        self.client.failures = 1
        self.sender.publish({'kind': 'no_repository', 'path': '/tmp/project'})
        self.start()
        self.wait_for(lambda: self.sender.pending is None)
        self.assertEqual([v for v, _ in self.client.calls], [1, 1])
        self.sender.publish({'path': '/tmp/project', 'kind': 'no_repository'})
        self.assertEqual(self.sender.version, 1)
        self.assertFalse(self.sender.pending_path.exists())

    def test_late_ack_does_not_remove_newer_pending(self):
        self.client.release = threading.Event()
        self.sender.publish({'value': 1})
        self.start()
        self.assertTrue(self.client.entered.wait(2))
        self.sender.publish({'value': 2})
        saved = json.loads(self.sender.pending_path.read_text())
        self.assertEqual(saved['version'], 2)
        self.assertNotIn('secret', self.sender.pending_path.read_text())
        self.client.release.set()
        self.wait_for(lambda: self.sender.pending is None)
        self.assertEqual([v for v, _ in self.client.calls], [1, 2])

    def test_offline_queue_keeps_only_latest(self):
        self.client.failures = 100
        self.sender.publish({'value': 1})
        self.sender.publish({'value': 2})
        self.sender.publish({'value': 3})
        self.start()
        self.assertTrue(self.client.entered.wait(2))
        self.assertEqual(json.loads(self.sender.pending_path.read_text())['version'], 3)
        self.client.failures = 0
        self.wait_for(lambda: self.sender.pending is None)
        self.assertTrue(all(version == 3 for version, _ in self.client.calls))

    def test_invalidated_connection_stops_retries_but_keeps_state(self):
        self.client.permanent = True
        self.sender.publish({'value': 1})
        self.start()
        self.wait_for(lambda: self.sender.halted)
        self.sender.publish({'value': 2})
        self.assertEqual(len(self.client.calls), 1)
        self.assertEqual(json.loads(self.sender.pending_path.read_text())['version'], 2)

    def test_new_generation_replaces_old_disk_queue_without_key(self):
        self.sender.publish({'value': 'old'})
        old_path = self.sender.pending_path
        newer = SnapshotSender(self.client, Connection(self.connection.session_id, 3, 'new-secret'),
                               self.temp.name, self.temp.name)
        newer.publish({'value': 'current'})
        self.assertFalse(old_path.exists())
        data = json.loads(newer.pending_path.read_text())
        self.assertEqual((data['generation'], data['version']), (3, 1))
        self.assertNotIn('key', data)

    def test_storage_error_keeps_pending_in_memory(self):
        with patch.object(Path, 'mkdir', side_effect=OSError('disk unavailable')):
            self.sender.publish({'value': 1})
        self.assertIsNotNone(self.sender.pending)
        self.assertIsNotNone(self.sender.storage_error)
        self.assertIn('на диск', self.sender.summary())
        self.start()
        self.wait_for(lambda: self.sender.pending is None)

    def test_close_does_not_wait_for_retry_delay(self):
        self.client.failures = 100
        self.sender.publish({'value': 1})
        self.start()
        self.assertTrue(self.client.entered.wait(2))
        started = time.monotonic()
        self.sender.close()
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertTrue(self.sender.pending_path.exists())


if __name__ == '__main__':
    unittest.main()
