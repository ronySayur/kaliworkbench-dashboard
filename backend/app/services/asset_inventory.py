from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset


def diff_asset_snapshots(
    previous: list[dict[str, Any]], current: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    prev_map = {str(a.get("identifier")): a for a in previous}
    curr_map = {str(a.get("identifier")): a for a in current}

    added = [a for ident, a in curr_map.items() if ident not in prev_map]
    removed = [a for ident, a in prev_map.items() if ident not in curr_map]
    changed = []
    for ident in set(prev_map) & set(curr_map):
        before, after = prev_map[ident], curr_map[ident]
        if before.get("fingerprint") != after.get("fingerprint"):
            changed.append({"before": before, "after": after})
    return {"added": added, "removed": removed, "changed": changed}


async def upsert_workspace_assets(
    session: AsyncSession, workspace_id: int, snapshot: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    result = await session.execute(select(Asset).where(Asset.workspace_id == workspace_id))
    existing = list(result.scalars().all())
    prev_dicts = [
        {"identifier": a.identifier, "fingerprint": a.fingerprint, "asset_type": a.asset_type}
        for a in existing
    ]
    current = [
        {
            "identifier": str(item.get("identifier")),
            "fingerprint": str(item.get("fingerprint")),
            "asset_type": str(item.get("asset_type") or "host"),
            "metadata": item.get("metadata") or {},
        }
        for item in snapshot
        if item.get("identifier") and item.get("fingerprint")
    ]

    diff = diff_asset_snapshots(prev_dicts, current)
    now = datetime.now(timezone.utc)
    curr_map = {item["identifier"]: item for item in current}

    for asset in existing:
        item = curr_map.get(asset.identifier)
        if item:
            asset.fingerprint = item["fingerprint"]
            asset.metadata_json = json.dumps(item.get("metadata") or {}, ensure_ascii=False)
            asset.last_seen = now

    existing_idents = {a.identifier for a in existing}
    for item in current:
        if item["identifier"] not in existing_idents:
            session.add(
                Asset(
                    workspace_id=workspace_id,
                    asset_type=item["asset_type"],
                    identifier=item["identifier"],
                    fingerprint=item["fingerprint"],
                    metadata_json=json.dumps(item.get("metadata") or {}, ensure_ascii=False),
                )
            )

    return diff


async def list_workspace_assets(session: AsyncSession, workspace_id: int) -> list[Asset]:
    result = await session.execute(
        select(Asset).where(Asset.workspace_id == workspace_id).order_by(Asset.identifier)
    )
    return list(result.scalars().all())
