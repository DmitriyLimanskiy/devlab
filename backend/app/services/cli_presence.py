"""Короткая аренда присутствия CLI, без изменения снимков и схемы БД."""
import time
from uuid import UUID


class CliPresence:
    ttl = 35

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.connections: dict[UUID, tuple[int, float]] = {}

    def remaining(self, session_id, generation):
        entry = self.connections.get(session_id)
        if entry is None or entry[0] != generation:
            return 0.0
        remaining = max(0.0, entry[1] - self.clock())
        if not remaining:
            self.connections.pop(session_id, None)
        return remaining

    def touch(self, session_id, generation):
        was_connected = self.remaining(session_id, generation) > 0
        self.connections[session_id] = (generation, self.clock() + self.ttl)
        return not was_connected

    def remove(self, session_id, generation=None):
        entry = self.connections.get(session_id)
        if entry is not None and (generation is None or entry[0] == generation):
            del self.connections[session_id]
            return True
        return False


presence = CliPresence()
