import asyncio
from uuid import UUID

from app.services.practice.practice_events import PracticeEvents
from fastapi import WebSocket, WebSocketDisconnect


class EventStream:
    @staticmethod
    async def stream_events(
        websocket: WebSocket, session_id: UUID, bus: PracticeEvents
    ) -> None:
        """Передавать события и ping по WebSocket с очисткой задач при отключении"""
        await websocket.accept()
        with bus.subscribe(session_id) as queue:
            # ready отправляется после регистрации, затем браузер читает HTTP-снимок
            await websocket.send_json({"type": "ready"})
            receiver = asyncio.create_task(websocket.receive_text())
            pending = None
            try:
                while True:
                    pending = asyncio.create_task(queue.get())
                    done, _ = await asyncio.wait(
                        {receiver, pending},
                        timeout=20,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if receiver in done:
                        receiver.result()
                        receiver = asyncio.create_task(websocket.receive_text())
                    if pending in done:
                        await websocket.send_json(pending.result())
                    else:
                        pending.cancel()
                        await asyncio.gather(pending, return_exceptions=True)
                    if not done:
                        await websocket.send_json({"type": "ping"})
            except (WebSocketDisconnect, RuntimeError):
                pass
            finally:
                receiver.cancel()
                if pending is not None:
                    pending.cancel()
                await asyncio.gather(
                    receiver, *([pending] if pending else []), return_exceptions=True
                )
