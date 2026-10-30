import sys
from pathlib import Path
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from devlab.api import ApiError
from devlab.presence import PresenceReporter


class PresenceTest(unittest.TestCase):
    def test_background_heartbeat_and_clean_disconnect(self):
        class Client:
            timeout = .1
            def __init__(self):
                self.called = threading.Event()
                self.calls = []
            def presence(self, connection, disconnect=False):
                self.calls.append(disconnect)
                self.called.set()
        client = Client()
        reporter = PresenceReporter(client, object(), interval=.01)
        reporter.start()
        self.assertTrue(client.called.wait(1))
        reporter.close()
        self.assertFalse(client.calls[0])
        self.assertTrue(client.calls[-1])
        self.assertFalse(reporter.thread.is_alive())

    def test_invalid_key_stops_heartbeat_without_reconnect(self):
        class Client:
            timeout = .1
            def __init__(self):
                self.calls = 0
            def presence(self, connection, disconnect=False):
                self.calls += 1
                raise ApiError('Недействующий ключ', retryable=False)
        client = Client()
        reporter = PresenceReporter(client, object(), interval=.01)
        reporter.start()
        reporter.thread.join(1)
        reporter.close()
        self.assertEqual(client.calls, 1)
