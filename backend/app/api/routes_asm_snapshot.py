from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.schemas.asm_pipeline import AsmPipelineRequest
from app.schemas.asm_snapshot import (
    AsmSnapshotDiffOut,
    AsmSnapshotDiffRequest,
    AsmSnapshotOut,
)
from app.services.asm_pipeline import run_pipeline
from app.services.asset_snapshot import diff_snapshots
from app.services.scope_guard import ensure_target_allowed

router = APIRouter(prefix="/api", tags=["asm-snapshot"], dependencies=[Depends(verify_token)])


@router.post("/asm/snapshot", response_model=AsmSnapshotOut)
async def create_asm_snapshot(payload: AsmPipelineRequest, session: AsyncSession = Depends(get_db)) -> AsmSnapshotOut:
    await ensure_target_allowed(
        session,
        workspace_id=payload.workspace_id,
        target=payload.target,
        module="asm",
        command_args=payload.commands,
    )
    results = await run_pipeline(payload.commands, payload.timeout)
    return AsmSnapshotOut(results=results)


@router.post("/asm/snapshot/diff", response_model=AsmSnapshotDiffOut)
async def create_asm_snapshot_diff(payload: AsmSnapshotDiffRequest) -> AsmSnapshotDiffOut:
    diff = diff_snapshots(payload.snapshot_a, payload.snapshot_b)
    return AsmSnapshotDiffOut(**diff)
