"""Последнее оперативное состояние и допуск CLI в памяти одного процесса"""

import hashlib
import secrets

from fastapi import HTTPException

from .practice_events import PracticeEvents


class WorktreeEvents(PracticeEvents):
    def publish(self, session_id, state):
        # Для оперативных данных важен последний пакет, а не все переходы
        for queue in self.listeners.get(session_id, ()):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait({"type": "worktree_changed", "worktree": state})


class LiveWorktree:
    def __init__(self):
        self.connections = {}
        self.states = {}
        self.events = WorktreeEvents()

    def bind(self, session_id, generation, key_hash):
        current = self.connections.get(session_id)
        if current and current[0] > generation:
            raise HTTPException(409, "Поколение подключения больше не действует")
        if current != (generation, key_hash):
            self.connections[session_id] = (generation, key_hash)
            self.states.pop(session_id, None)
            self.events.publish(session_id, self.read(session_id))

    def authorize(self, session_id, generation, credentials):
        if credentials is None:
            raise HTTPException(401, "Требуется ключ подключения")
        current = self.connections.get(session_id)
        if current is None:
            return False
        if current[0] != generation:
            raise HTTPException(409, "Поколение подключения больше не действует")
        digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        if not secrets.compare_digest(digest, current[1]):
            raise HTTPException(401, "Неверный ключ подключения")
        return True

    def publish(self, request):
        saved = self.states.get(request.session_id)
        state = request.state.model_dump(mode="json")
        if saved and request.version <= saved["version"]:
            if request.version == saved["version"] and state == saved["state"]:
                return saved
            raise HTTPException(409, "Версия оперативного состояния устарела")
        saved = dict(
            session_id=str(request.session_id),
            generation=request.generation,
            version=request.version,
            state=state,
        )
        self.states[request.session_id] = saved
        self.events.publish(request.session_id, saved)
        return saved

    def read(self, session_id):
        generation = self.connections.get(session_id, (0, None))[0]
        return self.states.get(
            session_id,
            dict(
                session_id=str(session_id), generation=generation, version=0, state=None
            ),
        )


live_worktree = LiveWorktree()
