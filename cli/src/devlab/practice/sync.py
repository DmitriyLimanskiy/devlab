import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path

from devlab.cli.api import ApiError


class SnapshotSender:
    def __init__(
        self, client, connection, folder, state_dir=None, retry_delay=1, max_delay=30
    ):
        self.client, self.connection = client, connection
        root = Path(
            state_dir
            or os.environ.get("DEVLAB_STATE_DIR")
            or Path.home() / "Library" / "Application Support" / "DevLab"
        )
        identity = (
            f"{client.server_url}\n{connection.session_id}\n{Path(folder).resolve()}"
        )
        name = hashlib.sha256(identity.encode()).hexdigest()
        self.state_dir = root.resolve()
        self.identity = name
        self.pending_path = (
            self.state_dir / "pending" / f"{name}-{connection.generation}.json"
        )
        self.condition = threading.Condition()
        self.queue = []
        self.last_state = None
        self.version = 0
        self.closed = self.halted = False
        self.error = self.storage_error = None
        self.retry_delay, self.max_delay = retry_delay, max_delay
        self.thread = threading.Thread(target=self.run, daemon=True)

    @property
    def pending(self):
        return self.queue[0] if self.queue else None

    def start(self):
        self.thread.start()

    def persist(self):
        """Вызывается под condition; ключ не входит в сохраняемое тело запроса"""
        temporary = None
        try:
            self.pending_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.pending_path.parent, prefix=".pending-", delete=False
            ) as stream:
                temporary = Path(stream.name)
                json.dump(self.queue, stream, ensure_ascii=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.pending_path)
            self.storage_error = None
        except OSError:
            self.storage_error = "Не удалось сохранить неподтверждённый снимок на диск"
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def publish(self, state):
        # Снимок копируется: новые состояния не должны менять тело повторного запроса
        state = {**state, "files": []} if state.get("kind") == "repository" else state
        canonical = json.dumps(state, sort_keys=True, ensure_ascii=True)
        with self.condition:
            if self.closed or canonical == self.last_state:
                return
            self.last_state = canonical
            self.version += 1
            self.queue.append(
                {
                    "schema_version": 1,
                    "session_id": self.connection.session_id,
                    "generation": self.connection.generation,
                    "version": self.version,
                    "state": json.loads(canonical),
                }
            )
            self.persist()
            self.condition.notify_all()

    def run(self):
        delay = self.retry_delay
        while True:
            with self.condition:
                self.condition.wait_for(
                    lambda: (
                        self.closed or (self.pending is not None and not self.halted)
                    )
                )
                if self.closed:
                    return
                payload = self.pending
                if self.storage_error:
                    self.persist()
            try:
                self.client.send_snapshot(
                    self.connection, payload["state"], payload["version"]
                )
            except ApiError as error:
                with self.condition:
                    self.error = str(error)
                    if not error.retryable:
                        # Не менять поколение автоматически при отзыве ключа/конфликте
                        self.halted = True
                        continue
                    self.condition.wait_for(
                        lambda payload=payload: (
                            self.closed or self.pending is not payload
                        ),
                        timeout=delay,
                    )
                delay = min(delay * 2, self.max_delay)
            else:
                with self.condition:
                    self.error = None
                    # Позднее подтверждение старой версии не удаляет новую из очереди
                    if self.pending is payload:
                        self.queue.pop(0)
                        if self.queue:
                            self.persist()
                        else:
                            try:
                                self.pending_path.unlink(missing_ok=True)
                                self.storage_error = None
                            except OSError:
                                self.storage_error = (
                                    "Подтверждённый файл очереди не удалось удалить"
                                )
                    self.condition.notify_all()
                delay = self.retry_delay

    def close(self):
        with self.condition:
            if self.closed:
                return
            # Дать очереди снимков короткую возможность уйти при нормальной сети
            # При сбое ограничить ожидание и оставить файл для следующего запуска
            if self.pending is not None and not self.halted:
                self.condition.wait_for(
                    lambda: self.pending is None or self.halted,
                    timeout=self.client.timeout + 0.2,
                )
            self.closed = True
            self.condition.notify_all()
        self.thread.join(timeout=0.1)

    def summary(self):
        with self.condition:
            try:
                old_queues = [
                    path
                    for path in self.pending_path.parent.glob(self.identity + "-*.json")
                    if path != self.pending_path
                ]
            except OSError:
                old_queues = []
            if self.pending is None:
                if old_queues:
                    return f"Остались неподтверждённые очереди прошлых подключений: {self.pending_path.parent} Старые поколения автоматически не отправляются"
                return None
            detail = self.error or "Снимок ещё не подтверждён"
            if self.storage_error:
                return f"{detail} {self.storage_error}"
            return f"{detail} Очередь снимков сохранена: {self.pending_path}"
