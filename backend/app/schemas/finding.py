from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int | None
    severity: str
    title: str
    endpoint_or_device: str | None
    evidence: Any | None = None
    is_new_diff: bool = False
    created_at: datetime
