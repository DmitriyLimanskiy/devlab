"""Локальное наблюдение: события bash, опрос файлов и периодическая сверка."""
import json
import os
import select
import threading
import time
import tempfile
from pathlib import Path

from .git_state import stable_state


def fingerprint(folder, excluded=None, internal_dir=None):
    entries = []
    for root, directories, files in os.walk(folder):
        if internal_dir is not None:
            directories[:] = [name for name in directories if Path(root) / name != internal_dir]
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
    def __init__(self, folder, events, snapshot, status_path=None, on_state=None, internal_dir=None):
        self.folder, self.events, self.snapshot = Path(folder).resolve(), events, Path(snapshot).resolve()
        self.status_path = Path(status_path) if status_path else self.snapshot.with_name("command-status.json")
        self.internal_dir = Path(internal_dir).resolve() if internal_dir is not None else None
        self.on_state = on_state
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.state = None
        self.version = 0
        self.preserve_existing = False

    def refresh(self, command_status=None):
        try:
            state = stable_state(self.folder)
            if state['kind'] == 'repository':
                relative = os.path.relpath(self.snapshot, state['path'])
                internal = (os.path.relpath(self.internal_dir, state['path']) + '/') if self.internal_dir else None
                state['files'] = [item for item in state['files'] if item['path'] != relative
                                  and not (internal and item['path'].startswith(internal))]
        except Exception as error:
            # Временная ошибка не заменяет последнее успешно прочитанное состояние.
            self.error = str(error)
            return
        self.error = None
        if self.preserve_existing and self.state is None:
            self.state = state
            try:
                version = json.loads(self.snapshot.read_text()).get('version', 0)
                self.version = version if type(version) is int and version >= 0 else 0
            except (OSError, ValueError, AttributeError):
                self.version = 0
            if self.on_state is not None:
                self.on_state(state)
            return
        if state != self.state:
            self.version += 1
            payload = {'generator': 'devlab-cli', 'version': self.version, 'updated_at': time.time(), 'state': state}
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', dir=self.snapshot.parent,
                                                 prefix='.devlab-state-', delete=False) as stream:
                    temporary = Path(stream.name)
                    json.dump(payload, stream, ensure_ascii=True, indent=2)
                os.replace(temporary, self.snapshot)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            self.state = state
            if self.on_state is not None:
                self.on_state(state)
        if command_status is not None:
            self.status_path.write_text(json.dumps(
                {'exit_code': command_status, 'completed_at': time.time()}))

    def run(self):
        previous = None
        pending = 0.0
        last_check = 0.0
        buffer = b''
        while not self.stop.is_set():
            ready, _, _ = select.select([self.events], [], [], 0.25)
            if ready:
                data = os.read(self.events, 4096)
                if not data:
                    break
                buffer += data
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
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
        self.refresh()

    def close(self):
        self.stop.set()
        self.thread.join()
