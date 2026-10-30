"""Настоящие HTTP/WS и PostgreSQL; отдельная схема, без изменения данных проекта"""

import asyncio
import json
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from unittest.mock import patch

import test_git_course
import uvicorn
from app.api.routes.practice import get_practice_state
from app.db.session import get_session
from app.main import app
from fastapi import Response
from websockets.asyncio.client import connect


class PracticeDeliveryTest(test_git_course.GitCourseTest):
    async def test_snapshot_http_websocket_duplicates_and_reconnect(self):
        await self.prepare_courses()
        course = await self.request()

        async def dependency():
            async with self.factory() as db:
                yield db

        app.dependency_overrides[get_session] = dependency
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
        with patch(
            "app.api.routes.practice.get_session_factory", return_value=self.factory
        ):
            task = asyncio.create_task(server.serve(sockets=[listener]))
            try:
                for _ in range(200):
                    if server.started:
                        break
                    await asyncio.sleep(0.01)
                self.assertTrue(server.started)

                async def request(path, body=None, key=None):
                    def send():
                        headers = {"Content-Type": "application/json"}
                        if key:
                            headers["Authorization"] = "Bearer " + key
                        req = urllib.request.Request(
                            f"http://127.0.0.1:{port}{path}",
                            data=json.dumps(body).encode()
                            if body is not None
                            else None,
                            headers=headers,
                        )
                        with urllib.request.urlopen(req, timeout=3) as response:
                            return json.load(response)

                    return await asyncio.to_thread(send)

                path = f"/api/v1/practice-sessions/{course.session_id}/snapshot"
                self.assertIsNone((await request(path))["snapshot"])
                ws_url = (
                    f"ws://127.0.0.1:{port}/ws/practice-sessions/{course.session_id}"
                )
                async with connect(ws_url) as ws:
                    self.assertEqual(json.loads(await ws.recv())["type"], "ready")
                    connection = await request(
                        "/api/v1/cli-connect", {"course_slug": "git"}
                    )
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "state_changed"
                    )
                    heartbeat = {
                        "session_id": str(course.session_id),
                        "generation": connection["generation"],
                    }
                    await request("/api/v1/cli-heartbeat", heartbeat, connection["key"])
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "state_changed"
                    )
                    self.assertTrue((await request(path))["cli_connected"])
                    await request("/api/v1/cli-heartbeat", heartbeat, connection["key"])
                    body = dict(
                        schema_version=1,
                        session_id=str(course.session_id),
                        generation=connection["generation"],
                        version=1,
                        state={"kind": "no_repository", "path": "/tmp/devlab-test"},
                    )
                    await request("/api/v1/cli-send-snapshot", body, connection["key"])
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "state_changed"
                    )
                    saved = await request(path)
                    self.assertEqual(saved["snapshot"]["state"], body["state"])
                    self.assertNotIn("key_hash", saved)
                    await request("/api/v1/cli-send-snapshot", body, connection["key"])
                    with self.assertRaises(TimeoutError):
                        await asyncio.wait_for(ws.recv(), 0.1)
                    self.assertEqual(
                        (await request(path))["snapshot"]["received_at"],
                        saved["snapshot"]["received_at"],
                    )
                # Состояние настоящего Git, включая commit, staged и untracked
                sys.path.insert(
                    0, str(Path(__file__).resolve().parents[2] / "cli" / "src")
                )
                from devlab.git_state import read_state

                with tempfile.TemporaryDirectory() as directory:
                    repo = Path(directory)

                    def git(*args):
                        return subprocess.run(
                            ["git", "-C", directory, *args],
                            check=True,
                            capture_output=True,
                        )

                    git("init", "-b", "main")
                    git("config", "user.name", "DevLab Test")
                    git("config", "user.email", "test@example.invalid")
                    (repo / "file").write_text("first")
                    git("add", "file")
                    git("commit", "-m", "first")
                    (repo / "file").write_text("second")
                    git("add", "file")
                    (repo / "untracked").write_text("new")
                    body["state"] = read_state(repo)
                body["version"] = 2
                await request("/api/v1/cli-send-snapshot", body, connection["key"])
                async with connect(ws_url) as ws:
                    self.assertEqual(json.loads(await ws.recv())["type"], "ready")
                    saved = (await request(path))["snapshot"]
                    self.assertEqual(saved["version"], 2)
                    from app.api.schemas.snapshot import SnapshotReq

                    self.assertEqual(
                        saved["state"],
                        SnapshotReq.model_validate(body).state.model_dump(mode="json"),
                    )
                # После ротации сохраняется старый снимок с явным поколением
                await request("/api/v1/cli-connect", {"course_slug": "git"})
                data = await request(path)
                self.assertGreater(data["generation"], data["snapshot"]["generation"])
            finally:
                server.should_exit = True
                await task
                app.dependency_overrides.clear()

    async def test_failed_commit_does_not_publish(self):
        from app.api.routes.cli import cli_connect, cli_send_state
        from app.api.schemas.cli import CliConnectReq
        from app.api.schemas.snapshot import SnapshotReq
        from app.services.practice_events import events
        from fastapi.security import HTTPAuthorizationCredentials

        await self.prepare_courses()
        course = await self.request()
        async with self.factory() as db:
            connection = await cli_connect(CliConnectReq(course_slug="git"), db)
        body = SnapshotReq(
            schema_version=1,
            session_id=course.session_id,
            generation=connection.generation,
            version=1,
            state={"kind": "no_repository", "path": "/tmp/test"},
        )
        with events.subscribe(course.session_id) as queue:
            async with self.factory() as db:
                with (
                    patch.object(
                        db, "commit", side_effect=RuntimeError("commit failed")
                    ),
                    self.assertRaises(RuntimeError),
                ):
                    await cli_send_state(
                        body,
                        db,
                        HTTPAuthorizationCredentials(
                            scheme="Bearer", credentials=connection.key
                        ),
                    )
                await db.rollback()
            self.assertTrue(queue.empty())
        async with self.factory() as db:
            result = await get_practice_state(course.session_id, Response(), db)
            self.assertIsNone(result.snapshot)

    async def test_presence_auth_and_no_snapshot_versions(self):
        from app.api.routes.cli import cli_connect, cli_disconnect, cli_heartbeat
        from app.api.schemas.cli import CliConnectReq, CliPresenceReq
        from app.services.cli_presence import presence
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        await self.prepare_courses()
        course = await self.request()
        async with self.factory() as db:
            connection = await cli_connect(CliConnectReq(course_slug="git"), db)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=connection.key
        )
        body = CliPresenceReq(
            session_id=course.session_id, generation=connection.generation
        )
        try:
            async with self.factory() as db:
                with self.assertRaises(HTTPException) as error:
                    await cli_heartbeat(body, db, None)
                self.assertEqual(error.exception.status_code, 401)
            async with self.factory() as db:
                await cli_heartbeat(body, db, credentials)
            async with self.factory() as db:
                result = await get_practice_state(course.session_id, Response(), db)
                self.assertTrue(result.cli_connected)
                self.assertGreater(result.cli_lease_seconds, 34)
                self.assertIsNone(result.snapshot)
            async with self.factory() as db:
                await cli_disconnect(body, db, credentials)
            self.assertEqual(presence.remaining(course.session_id, body.generation), 0)
            async with self.factory() as db:
                newer = await cli_connect(CliConnectReq(course_slug="git"), db)
            async with self.factory() as db:
                with self.assertRaises(HTTPException):
                    await cli_heartbeat(body, db, credentials)
            self.assertEqual(presence.remaining(course.session_id, newer.generation), 0)
        finally:
            presence.remove(course.session_id)

    async def test_missing_session_state(self):
        from uuid import uuid4

        from fastapi import HTTPException

        async with self.factory() as db:
            with self.assertRaises(HTTPException) as error:
                await get_practice_state(uuid4(), Response(), db)
            self.assertEqual(error.exception.status_code, 404)
