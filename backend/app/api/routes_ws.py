from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.api.deps import verify_ws_token
from app.db.engine import AsyncSessionLocal
from app.models.job import Job
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/jobs/{job_id}")
async def job_stream(websocket: WebSocket, job_id: int) -> None:
    if not verify_ws_token(websocket):
        await websocket.close(code=4401)
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
    if not job:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    stream = await ws_manager.get_or_create(job_id)
    await stream.subscribe(websocket)
    try:
        replay = stream.replay_events()
        if replay:
            await websocket.send_text(json.dumps({"type": "replay", "events": replay}))
        await websocket.send_text(
            json.dumps({"type": "status", "job_id": job_id, "status": job.status, "exit_code": job.exit_code})
        )
        while True:
            # Keep connection alive; client messages (if any) are ignored.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await stream.unsubscribe(websocket)
