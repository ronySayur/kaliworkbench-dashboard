from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    asset_type: str
    identifier: str
    fingerprint: str
    metadata_json: str | None
    first_seen: datetime
    last_seen: datetime


class AssetSnapshotDiffOut(BaseModel):
    added: list[dict[str, Any]] = Field(default_factory=list)
    removed: list[dict[str, Any]] = Field(default_factory=list)
    changed: list[dict[str, Any]] = Field(default_factory=list)


class AirodumpAnalyzeRequest(BaseModel):
    trusted_bssids: list[str] = Field(default_factory=list)
    csv_text: str


class AirodumpAnalyzeOut(BaseModel):
    networks: list[dict[str, Any]] = Field(default_factory=list)
    clients: list[dict[str, Any]] = Field(default_factory=list)
    anomalies: list[dict[str, Any]] = Field(default_factory=list)


class NmapParseRequest(BaseModel):
    nmap_xml: str


class NmapParseOut(BaseModel):
    assets: list[dict[str, Any]] = Field(default_factory=list)


class SubfinderParseRequest(BaseModel):
    output: str


class SubfinderParseOut(BaseModel):
    subdomains: list[str] = Field(default_factory=list)


class AssetSnapshotRequest(BaseModel):
    assets: list[dict[str, Any]] = Field(default_factory=list)
    workspace_id: int | None = None


class AssetSnapshotDiffRequest(BaseModel):
    previous: list[dict[str, Any]]
    current: list[dict[str, Any]]
