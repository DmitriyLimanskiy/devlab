import asyncio
import hashlib
import json
import socket
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from uuid import uuid4

import uvicorn
from websockets.asyncio.client import connect

from app.main import app
from app.services.cli.live_worktree import live_worktree


class WorktreeHttpTest(unittest.IsolatedAsyncioTestCase):
    async def test_memory_delivery_without_database_and_generation_rotation(self):
        """Проверить доставку файлов без БД и сброс состояния при смене поколения"""
        sid = uuid4()
        key = "test-worktree-key"
        live_worktree.bind(sid, 1, hashlib.sha256(key.encode()).hexdigest())
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        for _ in range(200):
            if server.started:
                break
            await asyncio.sleep(0.01)
        self.assertTrue(server.started)
        base = f"http://127.0.0.1:{port}"

        async def request(path, body=None, token=key):
            """Выполнить тестовый HTTP-запрос к backend"""

            def send():
                """Передать тестовый запрос или пакет и записать результат отправки"""
                req = urllib.request.Request(
                    base + path,
                    data=json.dumps(body).encode() if body is not None else None,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token,
                    },
                )
                with urllib.request.urlopen(req, timeout=2) as response:
                    return json.load(response)

            return await asyncio.to_thread(send)

        state = {
            "kind": "repository",
            "path": "/repo",
            "files": [
                {"path": "file", "index": "A", "worktree": "M", "conflict": False},
            ],
        }
        body = {"session_id": str(sid), "generation": 1, "version": 1, "state": state}
        path = f"/api/v1/practice-sessions/{sid}/worktree"
        try:
            with patch(
                "app.services.cli.authorization.get_session_factory",
                side_effect=AssertionError("База не должна вызываться"),
            ):
                self.assertIsNone((await request(path))["state"])
                async with connect(
                    f"ws://127.0.0.1:{port}/ws/practice-sessions/{sid}/worktree"
                ) as ws:
                    self.assertEqual(json.loads(await ws.recv())["type"], "ready")
                    ack = await request("/api/v1/cli-worktree", body)
                    self.assertEqual(ack["version"], 1)
                    self.assertNotIn("state", ack)
                    self.assertEqual(
                        json.loads(await ws.recv())["type"], "worktree_changed"
                    )
                    saved = await request(path)
                    self.assertEqual(saved["state"]["files"][0]["worktree"], "M")
                    await request("/api/v1/cli-worktree", body)
                    with self.assertRaises(TimeoutError):
                        await asyncio.wait_for(ws.recv(), 0.05)
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        await request("/api/v1/cli-worktree", body, token="wrong")
                    self.assertEqual(error.exception.code, 401)
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        await request(
                            "/api/v1/cli-worktree",
                            {**body, "state": {**state, "files": []}},
                        )
                    self.assertEqual(error.exception.code, 409)
                    await request(
                        "/api/v1/cli-worktree",
                        {**body, "version": 2, "state": {**state, "files": []}},
                    )
                    self.assertEqual((await request(path))["state"]["files"], [])
                    live_worktree.bind(sid, 2, hashlib.sha256(b"new-key").hexdigest())
                    self.assertIsNone((await request(path))["state"])
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        await request("/api/v1/cli-worktree", body)
                    self.assertEqual(error.exception.code, 409)
        finally:
            server.should_exit = True
            await task
            live_worktree.connections.pop(sid, None)
            live_worktree.states.pop(sid, None)

    async def test_cli_reads_state_json_and_pushes_external_edits_without_commands(
        self,
    ):
        """Проверить доставку внешних правок из state.json без команд CLI"""
        import os
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))
        from stack_forge.cli.api import ApiClient, Connection
        from stack_forge.practice.observer import Observer
        from stack_forge.practice.worktree import WorktreeSender

        sid, key = uuid4(), "periodic-test-key"
        live_worktree.bind(sid, 1, hashlib.sha256(key.encode()).hexdigest())
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        for _ in range(200):
            if server.started:
                break
            await asyncio.sleep(0.01)
        self.assertTrue(server.started)

        async def wait_files(predicate):
            """Дождаться ожидаемых статусов файлов в оперативном канале"""
            for _ in range(400):
                state = live_worktree.read(sid)["state"]
                if state and predicate(state.get("files", [])):
                    return state
                await asyncio.sleep(0.02)
            self.fail("Правки файлов не пришли по WebSocket")

        try:
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)

                def git(*args):
                    """Выполнить Git во временном тестовом репозитории"""
                    subprocess.run(
                        ["git", "-C", directory, *args], check=True, capture_output=True
                    )

                git("init", "-b", "main")
                git("config", "user.name", "Test")
                git("config", "user.email", "test@example.invalid")
                (folder / "file").write_text("base")
                git("add", ".")
                git("commit", "-m", "base")
                sender = WorktreeSender(
                    ApiClient(f"http://127.0.0.1:{port}", timeout=1),
                    Connection(str(sid), 1, key),
                    snapshot=folder / "state.json",
                    poll_interval=0.03,
                )
                read, write = os.pipe()
                observer = Observer(
                    folder,
                    read,
                    folder / "state.json",
                    Path(directory).parent / (str(sid) + "-status.json"),
                )
                observer.refresh()
                observer.thread.start()
                sender.start()
                try:
                    with patch(
                        "app.services.cli.authorization.get_session_factory",
                        side_effect=AssertionError("БД не нужна"),
                    ):
                        await wait_files(lambda files: files == [])
                        (folder / "file").write_text("IDE edit")
                        (folder / "new file").write_text("new")
                        state = await wait_files(lambda files: len(files) == 2)
                        statuses = {item["path"]: item for item in state["files"]}
                        self.assertEqual(statuses["file"]["worktree"], "M")
                        self.assertEqual(statuses["new file"]["index"], "?")
                        self.assertNotIn("commits", state)
                        git("add", ".")
                        await wait_files(
                            lambda files: any(
                                item["path"] == "file" and item["index"] == "M"
                                for item in files
                            )
                        )
                        old_version = live_worktree.read(sid)["version"]
                        observer.refresh()
                        await asyncio.sleep(0.15)
                        self.assertEqual(
                            live_worktree.read(sid)["version"], old_version
                        )
                finally:
                    await asyncio.to_thread(observer.close)
                    await asyncio.to_thread(sender.close)
                    os.close(read)
                    os.close(write)
        finally:
            server.should_exit = True
            await task
            live_worktree.connections.pop(sid, None)
            live_worktree.states.pop(sid, None)
