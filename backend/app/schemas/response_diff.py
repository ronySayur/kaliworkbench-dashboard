from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResponseDiffRequest(BaseModel):
    workspace_id: int
    target: str = Field(min_length=1, max_length=255)
    source_command: list[str] = Field(min_length=1)
    target_command: list[str] = Field(min_length=1)
    timeout: int = Field(default=10, ge=1, le=300)


class ResponseDiffOut(BaseModel):
    same: bool
    differences: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    source: str | None = None
    target: str | None = None
