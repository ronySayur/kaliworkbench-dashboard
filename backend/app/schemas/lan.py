from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LanInspectRequest(BaseModel):
    workspace_id: int
    target: str = Field(min_length=1, max_length=255)
    commands: list[list[str]] = Field(min_length=1)
    timeout: int = Field(default=30, ge=1, le=600)


class LanInspectOut(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)
