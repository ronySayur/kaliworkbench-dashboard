from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScopeCreate(BaseModel):
    target_type: str = Field(pattern="^(CIDR|Domain|IP|MAC)$")
    value: str = Field(min_length=1, max_length=255)
    notes: str | None = None


class ScopeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    target_type: str
    value: str
    notes: str | None
    created_at: datetime
