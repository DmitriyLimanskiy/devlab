import asyncio
import json
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import test_git_course
import uvicorn
from app.api.routes.practice.git_practice import (
    get_practice_state,
    get_snapshot_history,
)
from app.db.session import get_session
from app.main import app
from fastapi import Response
from websockets.asyncio.client import connect


class PracticeDeliveryTest(test_git_course.GitCourseTest):
    async def test_snapshot_http_websocket_duplicates_and_reconnect(self):
        """Проверить чтение снимков, события WebSocket, повторы и переподключение"""
        await self.prepare_courses()
        course = await self.request()

        async def dependency():
            """Предоставить приложению сессию из изолированной тестовой БД"""
            async with self.factory() as db:
                yield db

        app.dependency_overrides[get_session] = dependency
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
        with patch(
            "app.api.routes.practice.git_practice.get_session_factory",
            return_value=self.factory,
        ):
            task = asyncio.create_task(server.serve(sockets=[listener]))
            try:
                for _ in range(200):
                    if server.started:
                        break
                    await asyncio.sleep(0.01)
                self.assertTrue(server.started)

                async def request(path, body=None, key=None, method=None):
                    """Выполнить тестовый HTTP-запрос к backend"""

                    def send():
                        """Передать тестовый запрос или пакет и записать результат отправки"""
                        headers = {"Content-Type": "application/json"}
                        if key:
                            headers["Authorization"] = "Bearer " + key
                        req = urllib.request.Request(
                            f"http://127.0.0.1:{port}{path}",
                            data=json.dumps(body).encode()
                            if body is not None
                            else None,
                            headers=headers,
                            method=method,
                        )
                        with urllib.request.urlopen(req, timeout=3) as response:
                            return json.load(response)

                    return await asyncio.to_thread(send)

                opened = await request(
                    "/api/v1/git-course", {"course_slug": "git-sandbox"}
                )
                self.assertEqual(opened["session_id"], str(course.session_id))
                for body, status in [
                    (None, 422),
                    ({}, 422),
                    ({"course_slug": ""}, 422),
                    ({"course_slug": "python"}, 422),
                    ({"course_slug": "git-not-found"}, 404),
                ]:
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        await request("/api/v1/git-course", body, method="POST")
                    self.assertEqual(error.exception.code, status)

                path = f"/api/v1/practice-sessions/{course.session_id}/snapshot"
                self.assertIsNone((await request(path))["snapshot"])
                ws_url = (
                    f"ws://127.0.0.1:{port}/ws/practice-sessions/{course.session_id}"
                )
                async with connect(ws_url) as ws:
                    self.assertEqual(json.loads(await ws.recv())["type"], "ready")
                    connection = await request(
                        "/api/v1/cli/connect", {"course_slug": "git-sandbox"}
                    )
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "state_changed"
                    )
                    heartbeat = {
                        "session_id": str(course.session_id),
                        "generation": connection["generation"],
                    }
                    await request("/api/v1/cli/heartbeat", heartbeat, connection["key"])
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "state_changed"
                    )
                    self.assertTrue((await request(path))["cli_connected"])
                    await request("/api/v1/cli/heartbeat", heartbeat, connection["key"])
                    body = dict(
                        schema_version=1,
                        session_id=str(course.session_id),
                        generation=connection["generation"],
                        version=1,
                        state={
                            "kind": "no_repository",
                            "path": "/tmp/stack-forge-test",
                        },
                    )
                    await request("/api/v1/cli/send-snapshot", body, connection["key"])
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "state_changed"
                    )
                    saved = await request(path)
                    self.assertEqual(saved["snapshot"]["state"], body["state"])
                    self.assertNotIn("key_hash", saved)
                    await request("/api/v1/cli/send-snapshot", body, connection["key"])
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
                from stack_forge.practice.git_state import read_state

                with tempfile.TemporaryDirectory() as directory:
                    repo = Path(directory)

                    def git(*args):
                        """Выполнить Git во временном тестовом репозитории"""
                        return subprocess.run(
                            ["git", "-C", directory, *args],
                            check=True,
                            capture_output=True,
                        )

                    git("init", "-b", "main")
                    git("config", "user.name", "Stack Forge Test")
                    git("config", "user.email", "test@example.invalid")
                    (repo / "file").write_text("first")
                    git("add", "file")
                    git("commit", "-m", "first")
                    (repo / "file").write_text("second")
                    git("add", "file")
                    (repo / "untracked").write_text("new")
                    body["state"] = read_state(repo)
                body["version"] = 2
                await request("/api/v1/cli/send-snapshot", body, connection["key"])
                async with connect(ws_url) as ws:
                    self.assertEqual(json.loads(await ws.recv())["type"], "ready")
                    saved = (await request(path))["snapshot"]
                    self.assertEqual(saved["version"], 2)
                    from app.api.schemas.cli.snapshot import SnapshotReq

                    self.assertEqual(
                        saved["state"],
                        {
                            **SnapshotReq.model_validate(body).state.model_dump(
                                mode="json"
                            ),
                            "files": [],
                        },
                    )
                # После ротации сохраняется старый снимок с явным поколением
                await request("/api/v1/cli/connect", {"course_slug": "git-sandbox"})
                data = await request(path)
                self.assertGreater(data["generation"], data["snapshot"]["generation"])
            finally:
                server.should_exit = True
                await task
                app.dependency_overrides.clear()

    async def test_history_order_pagination_and_conflicting_retries(self):
        """Проверить порядок истории, границы страниц и конфликтующие повторы"""
        from app.api.routes.cli.cli import cli_connect, cli_send_state
        from app.api.schemas.cli.cli import CliConnectReq
        from app.api.schemas.cli.snapshot import SnapshotReq
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        await self.prepare_courses()
        course = await self.request()
        async with self.factory() as db:
            connection = await cli_connect(CliConnectReq(course_slug="git-sandbox"), db)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=connection.key
        )

        def body(version, path="/repo"):
            """Сформировать тело тестового запроса со снимком"""
            return SnapshotReq(
                schema_version=1,
                session_id=course.session_id,
                generation=connection.generation,
                version=version,
                state={"kind": "no_repository", "path": path},
            )

        ids = []
        for version in (1, 2, 3):
            async with self.factory() as db:
                ack = await cli_send_state(
                    body(version, f"/repo-{version}"), db, credentials
                )
                ids.append(ack.id)
        async with self.factory() as db:
            duplicate = await cli_send_state(body(1, "/repo-1"), db, credentials)
            self.assertEqual(duplicate.id, ids[0])
        async with self.factory() as db:
            with self.assertRaises(HTTPException) as error:
                await cli_send_state(body(1, "/different"), db, credentials)
            self.assertEqual(error.exception.status_code, 409)
        async with self.factory() as db:
            latest = await get_practice_state(course.session_id, Response(), db)
            self.assertEqual(latest.snapshot.version, 3)
            page = await get_snapshot_history(
                course.session_id,
                Response(),
                db,
                after_id=0,
                through_id=ids[-1],
                limit=2,
            )
            self.assertEqual([s.version for s in page.snapshots], [1, 2])
            self.assertTrue(page.has_more)
            page = await get_snapshot_history(
                course.session_id,
                Response(),
                db,
                after_id=ids[1],
                through_id=ids[-1],
                limit=2,
            )
            self.assertEqual([s.version for s in page.snapshots], [3])
            self.assertFalse(page.has_more)

    async def test_failed_commit_does_not_publish(self):
        """Проверить отсутствие события при неудачном commit в БД"""
        from app.api.routes.cli.cli import cli_connect, cli_send_state
        from app.api.schemas.cli.cli import CliConnectReq
        from app.api.schemas.cli.snapshot import SnapshotReq
        from app.services.practice.practice_events import events
        from fastapi.security import HTTPAuthorizationCredentials

        await self.prepare_courses()
        course = await self.request()
        async with self.factory() as db:
            connection = await cli_connect(CliConnectReq(course_slug="git-sandbox"), db)
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
        """Проверить авторизацию присутствия без увеличения версии снимка"""
        from app.api.routes.cli.cli import cli_connect, cli_disconnect, cli_heartbeat
        from app.api.schemas.cli.cli import CliConnectReq, CliPresenceReq
        from app.services.cli.cli_presence import presence
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        await self.prepare_courses()
        course = await self.request()
        async with self.factory() as db:
            connection = await cli_connect(CliConnectReq(course_slug="git-sandbox"), db)
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
                newer = await cli_connect(CliConnectReq(course_slug="git-sandbox"), db)
            async with self.factory() as db:
                with self.assertRaises(HTTPException):
                    await cli_heartbeat(body, db, credentials)
            self.assertEqual(presence.remaining(course.session_id, newer.generation), 0)
        finally:
            presence.remove(course.session_id)

    async def test_cli_client_resets_database_session(self):
        """Проверить реальный DELETE от CLI с авторизацией и очисткой связанных таблиц"""
        from app.db.models.practice.practice import PracticeSession, PracticeSnapshot
        from app.db.models.practice.repository import (
            GraphEvent,
            RepositoryCommit,
            SnapshotReceipt,
        )
        from sqlalchemy import func, select

        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))
        from stack_forge.cli.api import ApiClient, ApiError, Connection

        await self.prepare_courses()
        course = await self.request()

        async def dependency():
            """Предоставить HTTP-ручкам изолированную тестовую сессию БД"""
            async with self.factory() as db:
                yield db

        app.dependency_overrides[get_session] = dependency
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        try:
            for _ in range(200):
                if server.started:
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(server.started)
            client = ApiClient(f"http://127.0.0.1:{port}")
            connection = await asyncio.to_thread(client.connect, "git-sandbox")
            sha = "a" * 40
            state = {
                "kind": "repository",
                "path": "/repo",
                "head": sha,
                "branch": "main",
                "head_kind": "branch",
                "files": [],
                "commits": [{"id": sha, "parents": []}],
                "refs": [f"refs/heads/main {sha}"],
                "operations": [],
                "history_limit": 200,
            }
            await asyncio.to_thread(client.send_snapshot, connection, state, 1)
            models = (PracticeSnapshot, RepositoryCommit, GraphEvent, SnapshotReceipt)
            async with self.factory() as db:
                for model in models:
                    self.assertEqual(
                        await db.scalar(select(func.count()).select_from(model)), 1
                    )
            with self.assertRaises(ApiError):
                await asyncio.to_thread(
                    client.reset_practice,
                    Connection(
                        connection.session_id, connection.generation, "invalid-key"
                    ),
                )
            async with self.factory() as db:
                self.assertEqual(
                    await db.scalar(select(func.count()).select_from(PracticeSnapshot)),
                    1,
                )
            from uuid import uuid4

            reset_id = str(uuid4())
            newer = await asyncio.to_thread(client.reset_practice, connection, reset_id)
            self.assertEqual(newer.generation, connection.generation + 1)
            self.assertEqual(newer.key, connection.key)
            async with self.factory() as db:
                for model in models:
                    self.assertEqual(
                        await db.scalar(select(func.count()).select_from(model)),
                        1 if model is SnapshotReceipt else 0,
                    )
                session = await db.get(PracticeSession, course.session_id)
                self.assertEqual(session.generation, newer.generation)
            await asyncio.to_thread(client.send_snapshot, newer, state, 1)
            retry = await asyncio.to_thread(client.reset_practice, connection, reset_id)
            self.assertEqual(retry, newer)
            async with self.factory() as db:
                self.assertEqual(
                    await db.scalar(select(func.count()).select_from(PracticeSnapshot)),
                    1,
                )
            with self.assertRaises(ApiError):
                await asyncio.to_thread(client.send_snapshot, connection, state, 2)
            with self.assertRaises(ApiError):
                await asyncio.to_thread(client.reset_practice, connection, str(uuid4()))
        finally:
            server.should_exit = True
            await task
            app.dependency_overrides.pop(get_session, None)

    async def test_reset_inside_live_bash_keeps_session_and_updates_browser(self):
        """Проверить два сброса через живой PTY без смены bash и потери синхронизации"""
        import os
        import pty
        import select
        import shlex
        import time

        await self.prepare_courses()
        course = await self.request()

        async def dependency():
            """Предоставить ручкам локального сервера изолированную БД"""
            async with self.factory() as db:
                yield db

        app.dependency_overrides[get_session] = dependency
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
        task = asyncio.create_task(server.serve(sockets=[listener]))

        def exercise():
            """Управлять настоящим CLI через PTY параллельно HTTP-серверу теста"""
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory) / "repo"
                folder.mkdir()
                queue_root = Path(directory) / "queues"
                master, slave = pty.openpty()
                process = subprocess.Popen(
                    [sys.executable, "-m", "stack_forge"],
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    env=dict(
                        os.environ,
                        PYTHONPATH=str(Path(__file__).resolve().parents[2] / "cli/src"),
                        STACK_FORGE_SERVER_URL=f"http://127.0.0.1:{port}",
                        STACK_FORGE_OFFLINE="0",
                        STACK_FORGE_STATE_DIR=str(queue_root),
                        NO_COLOR="1",
                    ),
                )

                def until(expected):
                    """Прочитать PTY до ожидаемого текста с ограниченным ожиданием"""
                    data = b""
                    deadline = time.monotonic() + 20
                    while (
                        not (
                            expected in data
                            if isinstance(expected, bytes)
                            else expected.search(data)
                        )
                        and time.monotonic() < deadline
                    ):
                        if select.select([master], [], [], 0.1)[0]:
                            data += os.read(master, 65536)
                    self.assertTrue(
                        expected in data
                        if isinstance(expected, bytes)
                        else expected.search(data),
                        data.decode(errors="replace"),
                    )
                    return data

                def state_when(predicate):
                    """Дождаться подтверждённого состояния браузерного HTTP API"""
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/api/v1/practice-sessions/{course.session_id}/snapshot"
                        ) as response:
                            value = json.load(response)
                        if predicate(value):
                            return value
                        time.sleep(0.05)
                    self.fail("Состояние после сброса не доставлено")

                try:
                    until("Номер курса".encode())
                    os.write(master, b"1\n")
                    until("Папка проекта".encode())
                    os.write(master, str(folder).encode() + b"\n")
                    until(b" > ")
                    initial = state_when(lambda value: value["snapshot"] is not None)
                    os.write(master, b"echo BASH-PID:$$\n")
                    import re

                    pid_output = until(re.compile(rb"BASH-PID:\d+"))
                    bash_pid = re.findall(rb"BASH-PID:(\d+)", pid_output)[-1]
                    os.write(
                        master,
                        b"git init -b main && git -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -m first; printf 'COMMIT-DONE:%s\\n' $?\n",
                    )
                    until(b"COMMIT-DONE:0")
                    committed = state_when(
                        lambda value: (
                            value["snapshot"]["state"]["kind"] == "repository"
                            and len(value["snapshot"]["state"]["commits"]) == 1
                        )
                    )
                    self.assertGreater(
                        committed["graph_history_id"], initial["graph_history_id"]
                    )
                    for index in range(2):
                        command = (
                            shlex.quote(sys.executable)
                            + " -m stack_forge reset; printf 'RESET-DONE:%s\\n' $?\n"
                        )
                        os.write(master, command.encode())
                        output = until(b"RESET-DONE:0")
                        self.assertIn("История практики очищена".encode(), output)
                        self.assertNotIn("Выберите курс".encode(), output)
                        current = state_when(
                            lambda value: (
                                value["generation"] == initial["generation"] + index + 1
                                and value["snapshot"] is not None
                                and value["snapshot"]["generation"]
                                == value["generation"]
                            )
                        )
                        self.assertTrue(current["cli_connected"])
                        self.assertEqual(current["snapshot"]["version"], 1)
                        with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/api/v1/practice-sessions/{course.session_id}/snapshots?after_id=0"
                        ) as response:
                            history = json.load(response)
                        self.assertEqual(len(history["snapshots"]), 1)
                    os.write(master, b"echo BASH-PID:$$\n")
                    self.assertIn(
                        b"BASH-PID:" + bash_pid, until(re.compile(rb"BASH-PID:\d+"))
                    )
                    os.write(
                        master,
                        b"git -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -m after-reset; printf 'AFTER-DONE:%s\\n' $?\n",
                    )
                    until(b"AFTER-DONE:0")
                    state_when(
                        lambda value: (
                            len(value["snapshot"]["state"].get("commits", [])) == 2
                        )
                    )
                    self.assertFalse(list((queue_root / "pending").glob("*-1.json")))
                    os.write(master, b"exit\n")
                    until("Хорошего дня".encode())
                    self.assertEqual(process.wait(timeout=5), 0)
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                    os.close(master)
                    os.close(slave)

        try:
            for _ in range(200):
                if server.started:
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(server.started)
            await asyncio.to_thread(exercise)
        finally:
            server.should_exit = True
            await task
            app.dependency_overrides.pop(get_session, None)

    async def test_missing_session_state(self):
        """Проверить ответ при запросе состояния неизвестной сессии"""
        from uuid import uuid4

        from fastapi import HTTPException

        async with self.factory() as db:
            with self.assertRaises(HTTPException) as error:
                await get_practice_state(uuid4(), Response(), db)
            self.assertEqual(error.exception.status_code, 404)
