from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.workspace import Workspace
from app.schemas.asm import AssetOut, SubfinderParseOut, SubfinderParseRequest
from app.services.nmap import parse_nmap_xml
from app.services.subfinder import parse_subfinder_output
from app.services.asset_inventory import list_workspace_assets, upsert_workspace_assets

router = APIRouter(prefix="/api", tags=["asm-assets"], dependencies=[Depends(verify_token)])


@router.post("/asm/parse/nmap", response_model=dict)
async def parse_nmap_endpoint(payload: dict) -> dict:
    assets = parse_nmap_xml((payload or {}).get("nmap_xml", ""))
    return {"assets": assets}


@router.post("/asm/parse/subfinder", response_model=SubfinderParseOut)
async def parse_subfinder_endpoint(payload: SubfinderParseRequest) -> SubfinderParseOut:
    return SubfinderParseOut(subdomains=parse_subfinder_output(payload.output))


@router.get("/workspaces/{workspace_id}/assets", response_model=list[AssetOut])
async def list_assets(workspace_id: int, session: AsyncSession = Depends(get_db)) -> list[Asset]:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    return await list_workspace_assets(session, workspace_id)


@router.post("/workspaces/{workspace_id}/assets/sync", response_model=dict)
async def sync_assets(workspace_id: int, payload: dict, session: AsyncSession = Depends(get_db)) -> dict:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    snapshot = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(snapshot, list):
        raise HTTPException(status_code=400, detail="assets array is required")

    diff = await upsert_workspace_assets(session, workspace_id, snapshot)

    for item in diff.get("added", []):
        session.add(
            Finding(
                job_id=None,
                severity="MEDIUM",
                title=f"New open port detected: {item.get('identifier')}",
                endpoint_or_device=str(item.get("identifier")),
                evidence_json=json.dumps({"added_asset": item}, ensure_ascii=False),
                is_new_diff=True,
            )
        )

    await session.commit()
    return {"diff": diff}
