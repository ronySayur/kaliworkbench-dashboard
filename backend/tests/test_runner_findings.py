from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

import app.services.process_runner as runner_mod
from app.services.ws_manager import WSManager
from app.db.base import Base
from app.models.finding import Finding
from app.models.job import Job
from app.models.workspace import Workspace
from app.services.process_runner import process_runner

FIXTURE = Path(__file__).parent / "fixtures" / "gitleaks-sample.json"


@pytest.mark.asyncio
async def test_gitleaks_job_creates_findings(tmp_path, monkeypatch):
    db_path = tmp_path / "test_jobs.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    monkeypatch.setattr(runner_mod, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(runner_mod, "ws_manager", WSManager())

    async with session_factory() as session:
        ws = Workspace(name="findings-test", description=None)
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        job = Job(
            workspace_id=ws.id,
            module="gitleaks",
            status="queued",
            command_args=json.dumps({"command": ["cat", str(FIXTURE)], "target": "127.0.0.1", "timeout": 10}),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id
        ws_id = ws.id

    await process_runner._run_job(job_id, ["cat", str(FIXTURE)], timeout=10)

    async with session_factory() as session:
        job_res = await session.execute(select(Job).where(Job.id == job_id))
        job = job_res.scalar_one_or_none()
        assert job is not None
        assert job.status == "succeeded"
        findings_res = await session.execute(select(Finding).where(Finding.job_id == job_id))
        findings = list(findings_res.scalars().all())
        assert len(findings) == 1
        assert findings[0].severity == "HIGH"
        assert findings[0].title == "Hardcoded key"

    await engine.dispose()
