from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.schemas.asm_pipeline import AsmPipelineOut, AsmPipelineRequest
from app.services.asm_pipeline import run_pipeline
from app.services.scope_guard import ensure_target_allowed

router = APIRouter(prefix="/api", tags=["asm-pipeline"], dependencies=[Depends(verify_token)])


@router.post("/asm/pipeline", response_model=AsmPipelineOut)
async def create_asm_pipeline(payload: AsmPipelineRequest, session: AsyncSession = Depends(get_db)) -> AsmPipelineOut:
    await ensure_target_allowed(
        session,
        workspace_id=payload.workspace_id,
        target=payload.target,
        module="asm",
        command_args=payload.commands,
    )
    results = await run_pipeline(payload.commands, payload.timeout)
    return AsmPipelineOut(results=results)
