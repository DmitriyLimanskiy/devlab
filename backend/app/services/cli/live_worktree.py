import hashlib
import secrets

from app.services.practice.practice_events import PracticeEvents
from fastapi import HTTPException


class WorktreeEvents(PracticeEvents):
    def publish(self, session_id, state):
        """Передать подписчикам последнее состояние файлов вместо устаревшего пакета"""
        # Для оперативных данных важен последний пакет, а не все переходы
        for queue in self.listeners.get(session_id, ()):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait({"type": "worktree_changed", "worktree": state})


class LiveWorktree:
    def __init__(self):
        """Подготовить допуски CLI, оперативные состояния и шину файлов"""
        self.connections = {}
        self.states = {}
        self.events = WorktreeEvents()

    def bind(self, session_id, generation, key_hash):
        """Привязать ключ и поколение CLI, очищая состояние прошлого подключения"""
        current = self.connections.get(session_id)
        if current and current[0] > generation:
            raise HTTPException(409, "Поколение подключения больше не действует")
        if current != (generation, key_hash):
            self.connections[session_id] = (generation, key_hash)
            self.states.pop(session_id, None)
            self.events.publish(session_id, self.read(session_id))

    def authorize(self, session_id, generation, credentials):
        """Проверить ключ и поколение по допуску оперативного канала"""
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
        """Принять новую версию файлов или подтвердить идентичный повтор"""
        saved = self.states.get(request.session_id)
        state = request.state.model_dump(mode="json")
        if saved and request.version <= saved["version"]:
            if request.version == saved["version"] and state == saved["state"]:
                return saved
            raise HTTPException(409, "Версия оперативного состояния устарела")
        saved = {
            "session_id": str(request.session_id),
            "generation": request.generation,
            "version": request.version,
            "state": state,
        }
        self.states[request.session_id] = saved
        self.events.publish(request.session_id, saved)
        return saved

    def read(self, session_id):
        """Вернуть последнее состояние файлов либо пустой пакет текущего поколения"""
        generation = self.connections.get(session_id, (0, None))[0]
        return self.states.get(
            session_id,
            {
                "session_id": str(session_id),
                "generation": generation,
                "version": 0,
                "state": None,
            },
        )


live_worktree = LiveWorktree()
