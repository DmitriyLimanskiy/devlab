import json
import os
import select
import tempfile
import threading
import time
from pathlib import Path

from devlab.practice.git_state import stable_state


def fingerprint(folder, excluded=None, internal_dir=None):
    """Собрать признаки изменений файлов, исключая служебные пути"""
    entries = []
    for root, directories, files in os.walk(folder):
        if internal_dir is not None:
            directories[:] = [
                name for name in directories if Path(root) / name != internal_dir
            ]
        for name in directories + files:
            path = Path(root) / name
            if excluded is not None and path == excluded:
                continue
            try:
                stat = path.lstat()
                entries.append((str(path), stat.st_mtime_ns, stat.st_size, stat.st_ino))
            except OSError:
                continue
    return entries


class Observer:
    def __init__(
        self,
        folder,
        events,
        snapshot,
        status_path=None,
        on_state=None,
        on_worktree=None,
        internal_dir=None,
    ):
        """Подготовить наблюдение папки, локальный снимок и обработчики состояний"""
        self.folder, self.events, self.snapshot = (
            Path(folder).resolve(),
            events,
            Path(snapshot).resolve(),
        )
        self.status_path = (
            Path(status_path)
            if status_path
            else self.snapshot.with_name("command-status.json")
        )
        self.internal_dir = (
            Path(internal_dir).resolve() if internal_dir is not None else None
        )
        self.on_state = on_state
        self.on_worktree = on_worktree
        self.stop = threading.Event()
        self.lock = threading.RLock()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.state = None
        self.version = 0
        self.preserve_existing = False
        self.send_pending = True

    def read_state(self):
        """Прочитать актуальный Git без служебного снимка и каталога очереди"""
        state = stable_state(self.folder)
        if state["kind"] == "repository":
            relative = os.path.relpath(self.snapshot, state["path"])
            internal = (
                (os.path.relpath(self.internal_dir, state["path"]) + "/")
                if self.internal_dir
                else None
            )
            state["files"] = [
                item
                for item in state["files"]
                if item["path"] != relative
                and not (internal and item["path"].startswith(internal))
            ]
        return state

    def refresh(self, command_status=None):
        """Согласовать обновление снимка с переключением поколения при сбросе"""
        with self.lock:
            self._refresh(command_status)

    def _refresh(self, command_status=None):
        """Обновить локальный снимок и передать изменившееся состояние отправителям"""
        if command_status is not None:
            self.send_pending = True
        try:
            state = self.read_state()
        except Exception as error:  # noqa: BLE001 — ошибка наблюдения не останавливает оболочку
            # Временная ошибка не заменяет последнее успешно прочитанное состояние
            self.error = str(error)
            return
        self.error = None
        if self.preserve_existing and self.state is None:
            self.state = state
            try:
                version = json.loads(self.snapshot.read_text()).get("version", 0)
                self.version = version if type(version) is int and version >= 0 else 0
            except (OSError, ValueError, AttributeError):
                self.version = 0
            if self.on_worktree is not None:
                self.on_worktree(state)
            if self.on_state is not None:
                self.on_state(state)
            self.send_pending = False
            return
        if state != self.state:
            self.version += 1
            payload = {
                "generator": "devlab-cli",
                "version": self.version,
                "updated_at": time.time(),
                "state": state,
            }
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=self.snapshot.parent,
                    prefix=".devlab-state-",
                    delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    json.dump(payload, stream, ensure_ascii=True, indent=2)
                os.replace(temporary, self.snapshot)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            self.state = state
        # Опрос обновляет локальный файл, доставка привязана к завершению команды
        if self.send_pending:
            if self.on_worktree is not None:
                self.on_worktree(state)
            if self.on_state is not None:
                self.on_state(state)
            self.send_pending = False
        if command_status is not None:
            self.status_path.write_text(
                json.dumps({"exit_code": command_status, "completed_at": time.time()})
            )

    def run(self):
        """Обрабатывать завершения команд и периодически проверять внешние изменения"""
        previous = None
        pending = 0.0
        last_check = 0.0
        buffer = b""
        while not self.stop.is_set():
            ready, _, _ = select.select([self.events], [], [], 0.25)
            if ready:
                data = os.read(self.events, 4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.isdigit():
                        self.refresh(int(line))
            now = time.monotonic()
            current = fingerprint(self.folder, self.snapshot, self.internal_dir)
            if current != previous:
                previous = current
                pending = now + 0.3
            if (pending and now >= pending) or now - last_check >= 3:
                self.refresh()
                last_check = now
                pending = 0.0
        self.refresh(0)

    def close(self):
        """Остановить наблюдение и дождаться финального чтения состояния"""
        self.stop.set()
        self.thread.join()
