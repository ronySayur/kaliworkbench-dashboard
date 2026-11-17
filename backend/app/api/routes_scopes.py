from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_token
from app.db.engine import get_db
from app.models.allowed_scope import AllowedScope
from app.models.workspace import Workspace
from app.schemas.scope import ScopeCreate, ScopeOut

router = APIRouter(prefix="/api/workspaces/{workspace_id}/scopes", tags=["scopes"], dependencies=[Depends(verify_token)])


@router.get("", response_model=list[ScopeOut])
async def list_scopes(workspace_id: int, session: AsyncSession = Depends(get_db)) -> list[AllowedScope]:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    result = await session.execute(
        select(AllowedScope).where(AllowedScope.workspace_id == workspace_id).order_by(AllowedScope.id.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=ScopeOut, status_code=201)
async def create_scope(
    workspace_id: int, payload: ScopeCreate, session: AsyncSession = Depends(get_db)
) -> AllowedScope:
    ws = await session.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="workspace not found")
    scope = AllowedScope(
        workspace_id=workspace_id,
        target_type=payload.target_type,
        value=payload.value.strip(),
        notes=payload.notes,
    )
    session.add(scope)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="scope already exists")
    await session.refresh(scope)
    return scope


@router.delete("/{scope_id}", status_code=204)
async def delete_scope(workspace_id: int, scope_id: int, session: AsyncSession = Depends(get_db)) -> None:
    result = await session.execute(
        select(AllowedScope).where(AllowedScope.id == scope_id, AllowedScope.workspace_id == workspace_id)
    )
    scope = result.scalar_one_or_none()
    if not scope:
        raise HTTPException(status_code=404, detail="scope not found")
    await session.delete(scope)
    await session.commit()
