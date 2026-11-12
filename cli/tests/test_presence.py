import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stack_forge.features.session.presence import PresenceReporter
from stack_forge.shared.api import ApiError


class PresenceTest(unittest.TestCase):
    def test_background_heartbeat_and_clean_disconnect(self):
        """Проверить фоновый heartbeat и штатное отключение присутствия"""

        class Client:
            timeout = 0.1

            def __init__(self):
                """Подготовить состояние тестового клиента и сценарий сетевых ошибок"""
                self.called = threading.Event()
                self.calls = []

            def presence(self, connection, disconnect=False):
                """Записать тестовый heartbeat или имитировать ошибку ключа"""
                self.calls.append(disconnect)
                self.called.set()

        client = Client()
        reporter = PresenceReporter(client, object(), interval=0.01)
        reporter.start()
        self.assertTrue(client.called.wait(1))
        reporter.close()
        self.assertFalse(client.calls[0])
        self.assertTrue(client.calls[-1])
        self.assertFalse(reporter.thread.is_alive())

    def test_invalid_key_stops_heartbeat_without_reconnect(self):
        """Проверить остановку heartbeat при недействующем ключе без нового подключения"""

        class Client:
            timeout = 0.1

            def __init__(self):
                """Подготовить состояние тестового клиента и сценарий сетевых ошибок"""
                self.calls = 0

            def presence(self, connection, disconnect=False):
                """Записать тестовый heartbeat или имитировать ошибку ключа"""
                self.calls += 1
                raise ApiError("Недействующий ключ", retryable=False)

        client = Client()
        reporter = PresenceReporter(client, object(), interval=0.01)
        reporter.start()
        reporter.thread.join(1)
        reporter.close()
        self.assertEqual(client.calls, 1)
