from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BleScanRequest(BaseModel):
    timeout: float = Field(default=5.0, ge=1.0, le=30.0)


class BleScanOut(BaseModel):
    summary: dict[str, Any]
    devices: list[dict[str, Any]] = Field(default_factory=list)


class GattParseRequest(BaseModel):
    text: str


class GattParseOut(BaseModel):
    summary: dict[str, int]
    services: list[dict[str, Any]] = Field(default_factory=list)
