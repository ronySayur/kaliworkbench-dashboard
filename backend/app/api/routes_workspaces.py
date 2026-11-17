from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceOut, WorkspaceUpdate

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[WorkspaceOut])
async def list_workspaces(session: AsyncSession = Depends(get_db)) -> list[Workspace]:
    result = await session.execute(select(Workspace).order_by(Workspace.id.desc()))
    return list(result.scalars().all())


@router.post("", response_model=WorkspaceOut, status_code=201)
async def create_workspace(payload: WorkspaceCreate, session: AsyncSession = Depends(get_db)) -> Workspace:
    existing = await session.execute(select(Workspace).where(Workspace.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="workspace name already exists")
    ws = Workspace(name=payload.name, description=payload.description)
    session.add(ws)
    await session.commit()
    await session.refresh(ws)
    return ws


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(workspace_id: int, session: AsyncSession = Depends(get_db)) -> Workspace:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    return ws


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: int, payload: WorkspaceUpdate, session: AsyncSession = Depends(get_db)
) -> Workspace:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    if payload.name is not None:
        existing = await session.execute(
            select(Workspace).where(Workspace.name == payload.name, Workspace.id != workspace_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="workspace name already exists")
        ws.name = payload.name
    if payload.description is not None:
        ws.description = payload.description
    await session.commit()
    await session.refresh(ws)
    return ws


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(workspace_id: int, session: AsyncSession = Depends(get_db)) -> None:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    await session.delete(ws)
    await session.commit()
