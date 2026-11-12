import json
import os
import socket
import threading
from pathlib import Path

from cli.src.shared.api import ApiError


class LocalControl:
    def __init__(self, path, runtime):
        """Подготовить приватный локальный сокет управления открытым CLI"""
        self.path, self.runtime = Path(path), runtime
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(self.path))
        os.chmod(self.path, 0o600)
        self.listener.listen(1)
        self.listener.settimeout(0.2)
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        """Запустить управление только после fork оболочки"""
        self.thread.start()

    def run(self):
        """Обработать запрос сброса от дочерней команды без передачи ключа"""
        while not self.stopped.is_set():
            try:
                client, _ = self.listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with client:
                client.settimeout(1)
                try:
                    with client.makefile("rb") as stream:
                        request = json.loads(stream.readline(1025))
                    if request != {"command": "reset"}:
                        raise ValueError("Неизвестная команда")
                    if self.runtime is None:
                        raise ApiError("Для сброса требуется подключение CLI к серверу")
                    generation = self.runtime.reset()
                    response = {"ok": True, "generation": generation}
                except ApiError:
                    response = {
                        "ok": False,
                        "error": "Сброс не завершён — проверьте связь и повторите stack-forge reset",
                    }
                except (OSError, ValueError, TypeError):
                    response = {
                        "ok": False,
                        "error": "Не удалось выполнить локальный сброс",
                    }
                try:
                    client.sendall(
                        json.dumps(response, ensure_ascii=True).encode() + b"\n"
                    )
                except OSError:
                    # Результат сохраняется в основном процессе, даже если команда закрылась
                    pass

    @staticmethod
    def request_reset(path):
        """Попросить основной процесс сбросить практику через локальный сокет"""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(60)
                client.connect(str(path))
                client.sendall(b'{"command":"reset"}\n')
                with client.makefile("rb") as stream:
                    result = json.loads(stream.readline(4097))
            if not isinstance(result, dict) or result.get("ok") is not True:
                raise ApiError(
                    "Сброс не завершён — повторите stack-forge reset или перезапустите CLI"
                )
        except (OSError, ValueError, TypeError):
            raise ApiError(
                "Основной процесс Stack Forge недоступен — перезапустите CLI"
            ) from None

    def close(self):
        """Дождаться управления и удалить локальный сокет при выходе"""
        self.stopped.set()
        self.listener.close()
        self.thread.join()
        self.path.unlink(missing_ok=True)
