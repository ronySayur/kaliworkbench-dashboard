from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    workspace_id: int | None,
    job_id: int | None,
    module: str,
    action: str,
    status: str,
    command_args: Any = None,
) -> AuditLog:
    payload: str | None
    if command_args is None:
        payload = None
    elif isinstance(command_args, str):
        payload = command_args
    else:
        payload = json.dumps(command_args)
    entry = AuditLog(
        workspace_id=workspace_id,
        job_id=job_id,
        module=module,
        action=action,
        status=status,
        command_args=payload,
    )
    session.add(entry)
    await session.flush()
    return entry
