from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.schemas.ble import BleInspectOut, BleInspectRequest
from app.services.ble_scanner import run_capture
from app.services.scope_guard import ensure_target_allowed

router = APIRouter(prefix="/api", tags=["ble"], dependencies=[Depends(verify_token)])


@router.post("/ble/inspect", response_model=BleInspectOut)
async def ble_inspect(payload: BleInspectRequest, session: AsyncSession = Depends(get_db)) -> BleInspectOut:
    await ensure_target_allowed(
        session,
        workspace_id=payload.workspace_id,
        target=payload.target,
        module="ble",
        command_args=payload.commands,
    )
    results = await run_capture(payload.commands, payload.timeout)
    return BleInspectOut(results=results)
