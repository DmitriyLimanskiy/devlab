"""Присутствие CLI независимо от изменений Git и повторной доставки снимков"""
import threading

from .api import ApiError


class PresenceReporter:
    def __init__(self, client, connection, interval=10):
        self.client, self.connection, self.interval = client, connection, interval
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        permanent_error = False
        try:
            while not self.stopped.is_set():
                try:
                    self.client.presence(self.connection)
                except ApiError as error:
                    if not error.retryable:
                        permanent_error = True
                        return
                self.stopped.wait(self.interval)
        finally:
            if not permanent_error:
                try:
                    self.client.presence(self.connection, disconnect=True)
                except ApiError:
                    pass

    def close(self):
        self.stopped.set()
        self.thread.join(timeout=self.client.timeout + .2)
