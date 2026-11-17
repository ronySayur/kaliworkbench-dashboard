from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.schemas.lan import LanInspectOut, LanInspectRequest
from app.services.lan_tshark import run_capture
from app.services.scope_guard import ensure_target_allowed

router = APIRouter(prefix="/api", tags=["lan"], dependencies=[Depends(verify_token)])


@router.post("/lan/inspect", response_model=LanInspectOut)
async def lan_inspect(payload: LanInspectRequest, session: AsyncSession = Depends(get_db)) -> LanInspectOut:
    await ensure_target_allowed(
        session,
        workspace_id=payload.workspace_id,
        target=payload.target,
        module="lan",
        command_args=payload.commands,
    )
    results = await run_capture(payload.commands, payload.timeout)
    return LanInspectOut(results=results)
