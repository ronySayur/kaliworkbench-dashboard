from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.schemas.gatt import GattInspectOut, GattInspectRequest
from app.services.gatt_explorer import run_capture
from app.services.scope_guard import ensure_target_allowed

router = APIRouter(prefix="/api", tags=["gatt"], dependencies=[Depends(verify_token)])


@router.post("/gatt/inspect", response_model=GattInspectOut)
async def gatt_inspect(payload: GattInspectRequest, session: AsyncSession = Depends(get_db)) -> GattInspectOut:
    await ensure_target_allowed(
        session,
        workspace_id=payload.workspace_id,
        target=payload.target,
        module="gatt",
        command_args=payload.commands,
    )
    results = await run_capture(payload.commands, payload.timeout)
    return GattInspectOut(results=results)
