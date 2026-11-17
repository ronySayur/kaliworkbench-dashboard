from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    findings: list[dict[str, Any]] = Field(default_factory=list)


class ReportOut(BaseModel):
    generated_at: str
    total: int
    by_severity: dict[str, int] = Field(default_factory=dict)
