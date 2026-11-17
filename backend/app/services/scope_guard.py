from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit import write_audit_log
from app.services.scope_validator import validate_target


async def ensure_target_allowed(
    session: AsyncSession,
    *,
    workspace_id: int,
    target: str | None,
    module: str,
    command_args: object = None,
) -> None:
    if not target:
        raise HTTPException(
            status_code=400,
            detail="target is required and must be in workspace allowlist",
        )
    ok, reason = await validate_target(session, workspace_id, target)
    if not ok:
        await write_audit_log(
            session,
            workspace_id=workspace_id,
            job_id=None,
            module=module,
            action="execution_denied",
            status="denied",
            command_args={"target": target, "reason": reason, "command_args": command_args},
        )
        await session.commit()
        raise HTTPException(status_code=403, detail=f"target denied: {reason}")
