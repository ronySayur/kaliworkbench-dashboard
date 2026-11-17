from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.config import settings
from app.db.engine import get_db
from app.models.finding import Finding
from app.models.job import Job
from app.models.workspace import Workspace
from app.schemas.finding import FindingOut
from app.schemas.job import JobCreate, JobOut
from app.services.audit import write_audit_log
from app.services.html_report import render_job_report_html
from app.services.markdown_report import render_job_report_markdown
from app.services.pdf_report import render_job_report_pdf
from app.services.process_runner import process_runner
from app.services.sarif import generate_sarif
from app.services.scope_validator import validate_target

router = APIRouter(tags=["jobs"], dependencies=[Depends(verify_token)])


@router.get("/api/jobs", response_model=list[JobOut])
async def list_jobs(
    workspace_id: int | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> list[Job]:
    stmt = select(Job).order_by(Job.id.desc())
    if workspace_id is not None:
        stmt = stmt.where(Job.workspace_id == workspace_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/api/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: int, session: AsyncSession = Depends(get_db)) -> Job:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/api/jobs/{job_id}/findings", response_model=list[FindingOut])
async def list_job_findings(job_id: int, session: AsyncSession = Depends(get_db)) -> list[Finding]:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = await session.execute(
        select(Finding).where(Finding.job_id == job_id).order_by(Finding.id)
    )
    return list(result.scalars().all())


@router.post("/api/workspaces/{workspace_id}/jobs", response_model=JobOut, status_code=201)
async def create_job(workspace_id: int, payload: JobCreate, session: AsyncSession = Depends(get_db)) -> Job:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    if not payload.target:
        raise HTTPException(status_code=400, detail="target is required and must be in workspace allowlist")
    ok, reason = await validate_target(session, workspace_id, payload.target)
    if not ok:
        await write_audit_log(
            session,
            workspace_id=workspace_id,
            job_id=None,
            module=payload.module,
            action="create_job_denied",
            status="denied",
            command_args={"command": payload.command, "target": payload.target, "reason": reason},
        )
        await session.commit()
        raise HTTPException(status_code=403, detail=f"target denied: {reason}")

    timeout = payload.timeout or settings.job_timeout_default
    command_args = json.dumps(
        {"command": payload.command, "target": payload.target, "timeout": timeout},
        ensure_ascii=False,
    )
    job = Job(
        workspace_id=workspace_id,
        module=payload.module,
        status="queued",
        command_args=command_args,
    )
    session.add(job)
    await session.flush()
    await write_audit_log(
        session,
        workspace_id=workspace_id,
        job_id=job.id,
        module=payload.module,
        action="create_job",
        status="queued",
        command_args=command_args,
    )
    await session.commit()
    await session.refresh(job)

    await process_runner.start_job(job.id, payload.command, timeout)
    return job


@router.get("/api/jobs/{job_id}/sarif")
async def job_findings_sarif(job_id: int, session: AsyncSession = Depends(get_db)) -> dict:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = await session.execute(select(Finding).where(Finding.job_id == job_id).order_by(Finding.id))
    findings = []
    for f in result.scalars().all():
        try:
            evidence = json.loads(f.evidence_json) if f.evidence_json else None
        except Exception:
            evidence = None
        findings.append(
            {
                "severity": f.severity,
                "title": f.title,
                "evidence": evidence,
                "source": job.module,
                "job_id": job.id,
            }
        )
    return generate_sarif(findings)


@router.get("/api/jobs/{job_id}/report.md")
async def job_report_markdown(job_id: int, session: AsyncSession = Depends(get_db)):
    from fastapi.responses import Response

    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = await session.execute(select(Finding).where(Finding.job_id == job_id).order_by(Finding.id))
    findings = []
    for f in result.scalars().all():
        try:
            evidence = json.loads(f.evidence_json) if f.evidence_json else None
        except Exception:
            evidence = None
        findings.append({"severity": f.severity, "title": f.title, "evidence": evidence})
    body = render_job_report_markdown(
        job_id=job.id,
        module=job.module,
        status=job.status,
        workspace_id=job.workspace_id,
        command_args=job.command_args,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        findings=findings,
    )
    return Response(
        content=body,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="kaliworkbench-job-{job.id}.md"'},
    )


@router.get("/api/jobs/{job_id}/report.html")
async def job_report_html(job_id: int, session: AsyncSession = Depends(get_db)):
    from fastapi.responses import Response

    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = await session.execute(select(Finding).where(Finding.job_id == job_id).order_by(Finding.id))
    findings = []
    for f in result.scalars().all():
        try:
            evidence = json.loads(f.evidence_json) if f.evidence_json else None
        except Exception:
            evidence = None
        findings.append({"severity": f.severity, "title": f.title, "evidence": evidence})
    body = render_job_report_html(
        job_id=job.id,
        module=job.module,
        status=job.status,
        workspace_id=job.workspace_id,
        command_args=job.command_args,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        findings=findings,
    )
    return Response(
        content=body,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="kaliworkbench-job-{job.id}.html"'},
    )


@router.get("/api/jobs/{job_id}/report.pdf")
async def job_report_pdf(job_id: int, session: AsyncSession = Depends(get_db)):
    from fastapi.responses import Response

    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = await session.execute(select(Finding).where(Finding.job_id == job_id).order_by(Finding.id))
    findings = []
    for f in result.scalars().all():
        try:
            evidence = json.loads(f.evidence_json) if f.evidence_json else None
        except Exception:
            evidence = None
        findings.append({"severity": f.severity, "title": f.title, "evidence": evidence})
    body = render_job_report_pdf(
        job_id=job.id,
        module=job.module,
        status=job.status,
        workspace_id=job.workspace_id,
        command_args=job.command_args,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        findings=findings,
    )
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="kaliworkbench-job-{job.id}.pdf"'},
    )


@router.post("/api/jobs/{job_id}/cancel", response_model=JobOut)
async def cancel_job(job_id: int, session: AsyncSession = Depends(get_db)) -> Job:
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status not in ("queued", "running"):
        return job
    if process_runner.is_running(job_id):
        await process_runner.cancel_job(job_id)
    else:
        job.status = "cancelled"
        job.error = "cancelled before start"
        await write_audit_log(
            session,
            workspace_id=job.workspace_id,
            job_id=job.id,
            module=job.module,
            action="cancel",
            status="cancelled",
            command_args=job.command_args,
        )
        await session.commit()
        await session.refresh(job)
    return job
