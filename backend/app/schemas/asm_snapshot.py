from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AsmSnapshotRequest(BaseModel):
    commands: list[list[str]] = Field(min_length=1)
    timeout: int = Field(default=30, ge=1, le=600)


class AsmSnapshotOut(BaseModel):
    results: list[dict[str, Any]] = Field(default_factory=list)


class AsmSnapshotDiffRequest(BaseModel):
    snapshot_a: dict[str, Any]
    snapshot_b: dict[str, Any]


class AsmSnapshotDiffOut(BaseModel):
    same: bool
    differences: list[dict[str, Any]] = Field(default_factory=list)
