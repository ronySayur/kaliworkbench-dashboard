from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.schemas.report import ReportGenerateRequest, ReportOut
from app.services.report_generator import generate_report

router = APIRouter(prefix="/api", tags=["report"], dependencies=[Depends(verify_token)])


@router.post("/report/generate", response_model=ReportOut)
async def generate_report_endpoint(payload: ReportGenerateRequest) -> ReportOut:
    report = generate_report(payload.findings)
    return ReportOut(**report)
