import asyncio
import unittest
from uuid import uuid4

from app.services.practice_events import PracticeEvents


class EventsTest(unittest.IsolatedAsyncioTestCase):
    async def test_broadcast_coalescing_and_cleanup(self):
        events = PracticeEvents()
        session, other = uuid4(), uuid4()
        with (
            events.subscribe(session) as a,
            events.subscribe(session) as b,
            events.subscribe(other) as c,
        ):
            for _ in range(100):
                events.publish(session)
            self.assertEqual(a.qsize(), 1)
            self.assertEqual(b.qsize(), 1)
            self.assertTrue(c.empty())
            self.assertEqual(
                await asyncio.wait_for(a.get(), 1), {"type": "state_changed"}
            )
        self.assertFalse(events.listeners)


class PresenceTest(unittest.TestCase):
    def test_timeout_generation_and_disconnect(self):
        from app.services.cli_presence import CliPresence

        now = [100.0]
        presence = CliPresence(clock=lambda: now[0])
        session = uuid4()
        self.assertTrue(presence.touch(session, 1))
        now[0] += 10
        self.assertFalse(presence.touch(session, 1))
        self.assertEqual(presence.remaining(session, 1), 35)
        self.assertEqual(presence.remaining(session, 2), 0)
        self.assertFalse(presence.remove(session, 2))
        now[0] += 36
        self.assertEqual(presence.remaining(session, 1), 0)
        self.assertTrue(presence.touch(session, 2))
        self.assertTrue(presence.remove(session, 2))
