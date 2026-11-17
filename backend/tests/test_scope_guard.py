from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.allowed_scope import AllowedScope
from app.models.workspace import Workspace
from app.services.scope_guard import ensure_target_allowed


@pytest.fixture
async def db_session(tmp_path):
    db_path = tmp_path / "test_guard.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        ws = Workspace(name="guard-ws", description=None)
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        yield session, ws.id
    await engine.dispose()


@pytest.mark.asyncio
async def test_guard_denies_missing_target(db_session) -> None:
    session, ws_id = db_session
    with pytest.raises(HTTPException) as exc:
        await ensure_target_allowed(
            session,
            workspace_id=ws_id,
            target=None,
            module="asm",
            command_args=None,
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_guard_denies_unlisted_target_and_writes_audit_log(db_session) -> None:
    session, ws_id = db_session
    with pytest.raises(HTTPException) as exc:
        await ensure_target_allowed(
            session,
            workspace_id=ws_id,
            target="203.0.113.10",
            module="lan",
            command_args=[["echo", "x"]],
        )
    assert exc.value.status_code == 403

    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    result = await session.execute(select(AuditLog).where(AuditLog.action == "execution_denied"))
    entries = list(result.scalars().all())
    assert len(entries) == 1
    assert entries[0].module == "lan"


@pytest.mark.asyncio
async def test_guard_allows_listed_target(db_session) -> None:
    session, ws_id = db_session
    session.add(AllowedScope(workspace_id=ws_id, target_type="IP", value="127.0.0.1"))
    await session.commit()
    await ensure_target_allowed(
        session,
        workspace_id=ws_id,
        target="127.0.0.1",
        module="gatt",
        command_args=[["echo", "x"]],
    )
