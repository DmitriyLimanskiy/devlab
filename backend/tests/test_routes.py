import unittest

from app.main import app
from fastapi.routing import APIRoute, APIWebSocketRoute


class RoutesTest(unittest.TestCase):
    def test_http_contract_and_unique_registration(self):
        routes = [
            (method, route.path)
            for route in app.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        ]
        self.assertEqual(len(routes), len(set(routes)))
        self.assertEqual(
            set(routes),
            {
                ("GET", "/api/v1/catalog"),
                ("POST", "/api/v1/git-course"),
                ("POST", "/api/v1/cli-connect"),
                ("POST", "/api/v1/cli-send-snapshot"),
                ("POST", "/api/v1/cli-heartbeat"),
                ("POST", "/api/v1/cli-disconnect"),
                ("POST", "/api/v1/cli-worktree"),
                ("GET", "/api/v1/practice-sessions/{session_id}/snapshot"),
                ("GET", "/api/v1/practice-sessions/{session_id}/snapshots"),
                ("GET", "/api/v1/practice-sessions/{session_id}/worktree"),
            },
        )

    def test_websocket_contract_and_unique_registration(self):
        routes = [
            route.path for route in app.routes if isinstance(route, APIWebSocketRoute)
        ]
        self.assertEqual(len(routes), len(set(routes)))
        self.assertEqual(
            set(routes),
            {
                "/ws/cli-worktree",
                "/ws/practice-sessions/{session_id}",
                "/ws/practice-sessions/{session_id}/worktree",
            },
        )
