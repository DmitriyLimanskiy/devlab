import threading
from subprocess import TimeoutExpired
from uuid import uuid4

from stack_forge.cli.api import ApiError
from stack_forge.cli.presence import PresenceReporter
from stack_forge.practice.git_state import UnstableRepository
from stack_forge.practice.sync import SnapshotSender
from stack_forge.practice.worktree import WorktreeSender


class PracticeRuntime:
    def __init__(self, sender, folder, snapshot):
        """Объединить отправители текущего подключения для согласованного сброса"""
        self.sender = sender
        self.folder, self.snapshot = folder, snapshot
        self.client, self.connection = sender.client, sender.connection
        self.presence = PresenceReporter(self.client, self.connection)
        self.worktree = WorktreeSender(self.client, self.connection, snapshot=snapshot)
        self.observer = None
        self.lock = threading.RLock()
        self.reset_lock = threading.Lock()
        self.resetting = False
        self.reset_id = self.confirmed_connection = None

    def start(self):
        """Запустить отправители после создания дочернего PTY"""
        self.worktree.start()
        self.presence.start()
        self.sender.start()

    def publish(self, state):
        """Передать снимок текущему отправителю вне процедуры сброса"""
        with self.lock:
            if not self.resetting:
                self.sender.publish(state)

    def seed(self, state):
        """Передать начальные файлы только действующему отправителю"""
        with self.lock:
            if not self.resetting:
                self.worktree.seed(state)

    def reset(self):
        """Сменить поколение, очистить очередь и возобновить отправители без выхода из bash"""
        with self.reset_lock:
            with self.lock:
                self.resetting = True
                if self.reset_id is None:
                    self.reset_id = str(uuid4())
            with self.observer.lock:
                self.sender.stop()
                self.worktree.stop()
                self.presence.stop()
                if self.confirmed_connection is None:
                    self.confirmed_connection = self.client.reset_practice(
                        self.connection, self.reset_id
                    )
                try:
                    self.sender.clear_pending()
                    state = self.observer.read_state()
                except (
                    OSError,
                    RuntimeError,
                    ValueError,
                    TimeoutExpired,
                    UnstableRepository,
                ) as error:
                    raise ApiError(
                        "Сброс подтверждён, но локальное состояние не подготовлено — повторите stack-forge reset"
                    ) from error
                connection = self.confirmed_connection
                sender = SnapshotSender(
                    self.client,
                    connection,
                    self.folder,
                    state_dir=self.sender.state_dir,
                    retry_delay=self.sender.retry_delay,
                    max_delay=self.sender.max_delay,
                )
                worktree = WorktreeSender(
                    self.client, connection, snapshot=self.snapshot
                )
                presence = PresenceReporter(self.client, connection)
                sender.publish(state)
                worktree.seed(state)
                with self.lock:
                    self.connection = connection
                    self.sender, self.worktree, self.presence = (
                        sender,
                        worktree,
                        presence,
                    )
                    self.reset_id = self.confirmed_connection = None
                    self.resetting = False
                    self.start()
                return connection.generation

    def close(self):
        """Завершить доставку текущего поколения при закрытии оболочки"""
        self.worktree.close()
        self.presence.close()
        self.sender.close()
