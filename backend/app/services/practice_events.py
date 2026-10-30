"""Уведомления об изменениях для одного процесса FastAPI.

Очередь хранит только сигнал перечитать БД, а не историю событий.
"""
import asyncio
from contextlib import contextmanager
from uuid import UUID


class PracticeEvents:
    def __init__(self):
        self.listeners: dict[UUID, set[asyncio.Queue]] = {}

    @contextmanager
    def subscribe(self, session_id: UUID):
        queue = asyncio.Queue(maxsize=1)
        self.listeners.setdefault(session_id, set()).add(queue)
        try:
            yield queue
        finally:
            self.listeners[session_id].discard(queue)
            if not self.listeners[session_id]:
                del self.listeners[session_id]

    def publish(self, session_id: UUID):
        for queue in self.listeners.get(session_id, ()):
            if not queue.full():
                queue.put_nowait({"type": "state_changed"})


events = PracticeEvents()
