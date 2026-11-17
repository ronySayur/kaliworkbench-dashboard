from __future__ import annotations

import asyncio
import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.services.process_runner as runner_mod
from app.db.base import Base
from app.models.job import Job
from app.models.workspace import Workspace
from app.services.process_runner import process_runner, RunningJob
from app.services.ws_manager import WSManager


@pytest.mark.asyncio
async def test_cancel_running_job_marks_cancelled(tmp_path, monkeypatch):
    db_path = tmp_path / "cancel.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    monkeypatch.setattr(runner_mod, "AsyncSessionLocal", factory)
    monkeypatch.setattr(runner_mod, "ws_manager", WSManager())

    async with factory() as session:
        ws = Workspace(name="cancel-ws", description=None)
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        job = Job(
            workspace_id=ws.id,
            module="generic",
            status="queued",
            command_args=json.dumps({"command": ["sleep", "30"], "target": "127.0.0.1", "timeout": 60}),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    task = asyncio.create_task(process_runner._run_job(job_id, ["sleep", "30"], timeout=60))
    # let the process spawn and register
    for _ in range(50):
        await asyncio.sleep(0.05)
        if process_runner.is_running(job_id):
            break
    assert process_runner.is_running(job_id)
    assert await process_runner.cancel_job(job_id) is True
    await asyncio.wait_for(task, timeout=10)

    async with factory() as session:
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        assert job is not None
        assert job.status == "cancelled"

    await engine.dispose()


@pytest.mark.asyncio
async def test_cancel_unknown_job_returns_false() -> None:
    assert await process_runner.cancel_job(999999) is False
