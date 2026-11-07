import json
import threading
import time
from pathlib import Path

from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.sync.client import connect


class WorktreeSender:
    def __init__(
        self,
        client,
        connection,
        snapshot=None,
        retry_delay=1,
        resend_interval=10,
        poll_interval=0.3,
        connector=connect,
    ):
        self.client, self.connection = client, connection
        self.snapshot = Path(snapshot) if snapshot is not None else None
        self.retry_delay, self.resend_interval = retry_delay, resend_interval
        self.poll_interval, self.connector = poll_interval, connector
        self.started_at = time.time()
        self.signature = None
        self.condition = threading.Condition()
        self.latest = None
        self.version = self.ack_version = 0
        self.closed = self.halted = False
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def publish(self, state):
        files = {"kind": state["kind"], "path": state["path"]}
        if state["kind"] == "repository":
            files["files"] = state["files"]
        with self.condition:
            if self.closed or (self.latest and self.latest[1] == files):
                return
            self.version += 1
            self.latest = (
                self.version,
                json.loads(json.dumps(files, ensure_ascii=True)),
            )
            self.condition.notify_all()

    def seed(self, state):
        # Начальное чтение нужно и при отказе перезаписывать старый state.json
        with self.condition:
            if self.latest is None:
                self.publish(state)

    def poll_snapshot(self):
        if self.snapshot is None:
            return
        try:
            stat = self.snapshot.stat()
            signature = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
            if signature == self.signature:
                return
            payload = json.loads(self.snapshot.read_text())
            # Ответ no на перезапись не должен отправить старую сессию из файла
            if (
                payload.get("generator") != "devlab-cli"
                or payload.get("updated_at", 0) < self.started_at
            ):
                return
            state = payload["state"]
            if state.get("kind") not in {
                "repository",
                "no_repository",
                "unavailable",
            } or not isinstance(state.get("path"), str):
                return
            if state["kind"] == "repository" and not isinstance(
                state.get("files"), list
            ):
                return
            self.publish(state)
            self.signature = signature
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # Атомарная замена или временная ошибка файла не стирает последние данные
            return

    def _send_state(self, socket, payload):
        socket.send(
            json.dumps(
                {
                    "session_id": self.connection.session_id,
                    "generation": self.connection.generation,
                    "version": payload[0],
                    "state": payload[1],
                },
                ensure_ascii=True,
            )
        )
        ack = json.loads(socket.recv(timeout=self.client.timeout))
        if not isinstance(ack, dict):
            # Любой неверный формат подтверждения остаётся ошибкой значения
            raise ValueError("Нет подтверждения оперативного состояния")  # noqa: TRY004
        if ack.get("type") == "error":
            self.halted = ack.get("status") in {401, 409, 422}
            raise ValueError("Оперативное состояние отклонено")
        if (
            ack.get("type") != "ack"
            or ack.get("session_id") != self.connection.session_id
            or ack.get("generation") != self.connection.generation
            or ack.get("version") != payload[0]
        ):
            raise ValueError("Нет подтверждения оперативного состояния")

    def run(self):
        socket = None
        delay = self.retry_delay
        retry_at = resend_at = 0
        scheme = "wss" if self.client.server_url.startswith("https:") else "ws"
        url = (
            scheme
            + self.client.server_url[self.client.server_url.index(":") :]
            + "/ws/cli-worktree"
        )
        try:
            while True:
                self.poll_snapshot()
                with self.condition:
                    if self.closed:
                        return
                    payload = self.latest
                now = time.monotonic()
                if (
                    payload
                    and not self.halted
                    and now >= retry_at
                    and (
                        payload[0] > self.ack_version
                        or socket is None
                        or now >= resend_at
                    )
                ):
                    try:
                        if socket is None:
                            socket = self.connector(
                                url,
                                additional_headers={
                                    "Authorization": "Bearer " + self.connection.key
                                },
                                open_timeout=self.client.timeout,
                                close_timeout=0.2,
                                ping_interval=10,
                                ping_timeout=10,
                                proxy=None,
                                max_size=2_000_000,
                            )
                        self._send_state(socket, payload)
                    except (
                        OSError,
                        TimeoutError,
                        WebSocketException,
                        ValueError,
                        TypeError,
                    ) as error:
                        if (
                            isinstance(error, ConnectionClosed)
                            and error.rcvd
                            and error.rcvd.code == 1008
                        ):
                            self.halted = True
                        if socket is not None:
                            socket.close()
                            socket = None
                        retry_at = time.monotonic() + delay
                        delay = min(delay * 2, 30)
                    else:
                        with self.condition:
                            self.ack_version = max(self.ack_version, payload[0])
                            self.condition.notify_all()
                        resend_at = time.monotonic() + self.resend_interval
                        retry_at = 0
                        delay = self.retry_delay
                with self.condition:
                    if not self.closed:
                        self.condition.wait(timeout=self.poll_interval)
        finally:
            if socket is not None:
                socket.close()

    def close(self):
        self.poll_snapshot()
        with self.condition:
            if self.latest is not None and not self.halted:
                self.condition.notify_all()
                self.condition.wait_for(
                    lambda: self.ack_version >= self.version or self.halted,
                    timeout=self.client.timeout + 0.2,
                )
            self.closed = True
            self.condition.notify_all()
        self.thread.join(timeout=self.client.timeout + 0.5)
