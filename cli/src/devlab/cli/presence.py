import threading

from devlab.cli.api import ApiError


class PresenceReporter:
    def __init__(self, client, connection, interval=10):
        """Подготовить фоновое подтверждение присутствия CLI"""
        self.client, self.connection, self.interval = client, connection, interval
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        """Запустить поток подтверждения присутствия после создания PTY"""
        self.thread.start()

    def run(self):
        """Посылать heartbeat до остановки и завершить присутствие при штатном выходе"""
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
        """Остановить heartbeat с ограниченным ожиданием потока"""
        self.stopped.set()
        self.thread.join(timeout=self.client.timeout + 0.2)
