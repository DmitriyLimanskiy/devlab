import json
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stack_forge.features.git_practice.observer import Observer
from stack_forge.features.git_practice.runtime import PracticeRuntime
from stack_forge.features.git_practice.sync import SnapshotSender
from stack_forge.shared.api import ApiError, Connection


class PassiveWorktree:
    def __init__(self, client, connection, snapshot=None):
        """Подготовить тестовый канал файлов без сетевого соединения"""
        self.connection, self.latest = connection, None

    def start(self):
        """Обозначить запуск тестового канала без фоновой работы"""
        pass

    def seed(self, state):
        """Сохранить файлы свежего чтения для проверки после сброса"""
        self.latest = state

    def stop(self):
        """Обозначить остановку тестового канала"""
        pass

    def close(self):
        """Завершить тестовый канал без дополнительных операций"""
        pass


class RuntimeClient:
    timeout = 0.1
    server_url = "http://127.0.0.1:8080"

    def __init__(self):
        """Подготовить журнал отправок и воспроизводимую потерю ответа сброса"""
        self.calls, self.reset_calls, self.resets = [], [], {}
        self.lost_reply = False
        self.entered = threading.Event()
        self.release = None

    def send_snapshot(self, connection, state, version):
        """Записать поколение снимка с возможностью задержать старый запрос"""
        self.calls.append((connection.generation, version))
        self.entered.set()
        if self.release is not None and connection.generation == 1:
            self.release.wait(2)

    def presence(self, connection, disconnect=False):
        """Подтвердить присутствие без сетевых побочных действий"""
        pass

    def reset_practice(self, connection, reset_id):
        """Применить повторяемый сброс и при необходимости потерять первый ответ"""
        self.reset_calls.append(reset_id)
        value = self.resets.setdefault(
            reset_id,
            Connection(
                connection.session_id, connection.generation + 1, connection.key
            ),
        )
        if self.lost_reply:
            self.lost_reply = False
            raise ApiError("Ответ потерян")
        return value


class RuntimeTest(unittest.TestCase):
    def setUp(self):
        """Создать реальный репозиторий и управляемые отправители для сброса"""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.folder = root / "repo"
        self.folder.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main", str(self.folder)],
            check=True,
            capture_output=True,
        )
        self.client = RuntimeClient()
        self.connection = Connection("session", 1, "secret")
        sender = SnapshotSender(
            self.client, self.connection, self.folder, root / "queues"
        )
        self.old_path = sender.pending_path
        substitute = patch(
            "stack_forge.features.git_practice.runtime.WorktreeSender", PassiveWorktree
        )
        substitute.start()
        self.addCleanup(substitute.stop)
        self.runtime = PracticeRuntime(sender, self.folder, self.folder / "state.json")
        self.runtime.observer = Observer(self.folder, 0, self.folder / "state.json")
        self.runtime.start()
        self.addCleanup(self.runtime.close)

    def test_reset_discards_old_queue_and_seeds_new_generation(self):
        """Очистить старый файл и начать новое поколение с первой версии"""
        self.runtime.sender.halted = True
        self.runtime.publish({"kind": "no_repository", "path": str(self.folder)})
        self.assertTrue(self.old_path.exists())
        self.assertEqual(self.runtime.reset(), 2)
        self.assertEqual(self.runtime.connection.key, "secret")
        self.assertFalse(self.old_path.exists())
        self.assertEqual(self.runtime.sender.version, 1)
        self.assertEqual(self.runtime.worktree.latest["kind"], "repository")
        self.assertEqual(self.runtime.presence.connection.generation, 2)

    def test_lost_reply_keeps_queue_until_same_reset_is_confirmed(self):
        """Повторить тот же сброс после потери ответа без второго увеличения поколения"""
        self.runtime.sender.halted = True
        self.runtime.publish({"kind": "no_repository", "path": str(self.folder)})
        self.client.lost_reply = True
        with self.assertRaises(ApiError):
            self.runtime.reset()
        self.assertTrue(self.old_path.exists())
        self.assertTrue(self.runtime.resetting)
        self.runtime.publish({"value": "not queued during reset"})
        self.assertEqual(len(json.loads(self.old_path.read_text())), 1)
        self.assertEqual(self.runtime.reset(), 2)
        self.assertEqual(len(set(self.client.reset_calls)), 1)
        self.assertFalse(self.old_path.exists())

    def test_reset_waits_for_inflight_snapshot_before_rotating(self):
        """Дождаться старого HTTP-запроса перед сменой поколения и отправителя"""
        self.client.release = threading.Event()
        self.runtime.publish({"kind": "no_repository", "path": str(self.folder)})
        self.assertTrue(self.client.entered.wait(1))
        with ThreadPoolExecutor(max_workers=1) as executor:
            reset = executor.submit(self.runtime.reset)
            self.assertFalse(reset.done())
            self.client.release.set()
            self.assertEqual(reset.result(timeout=3), 2)
        self.runtime.sender.close()
        self.assertIn((2, 1), self.client.calls)
        self.assertEqual(self.client.calls[0], (1, 1))
