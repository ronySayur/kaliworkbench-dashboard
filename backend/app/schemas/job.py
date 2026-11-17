from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    module: str = Field(default="generic", min_length=1, max_length=100)
    command: list[str] = Field(min_length=1)
    target: str | None = None
    timeout: int | None = Field(default=None, ge=1, le=3600)


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    module: str
    status: str
    command_args: str
    pgid: int | None
    pid: int | None
    exit_code: int | None
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
