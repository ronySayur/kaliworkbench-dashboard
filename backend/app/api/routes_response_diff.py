from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.schemas.response_diff import ResponseDiffOut, ResponseDiffRequest
from app.services.response_diff import diff_json, run_pair
from app.services.scope_guard import ensure_target_allowed

router = APIRouter(prefix="/api", tags=["response-diff"], dependencies=[Depends(verify_token)])


@router.post("/response-diff", response_model=ResponseDiffOut)
async def create_response_diff(
    payload: ResponseDiffRequest,
    session: AsyncSession = Depends(get_db),
) -> ResponseDiffOut:
    await ensure_target_allowed(
        session,
        workspace_id=payload.workspace_id,
        target=payload.target,
        module="response-diff",
        command_args={"source_command": payload.source_command, "target_command": payload.target_command},
    )
    source, target_out = await run_pair(payload.source_command, payload.target_command, payload.timeout)
    diff = diff_json(source, target_out)
    return ResponseDiffOut(**diff)
