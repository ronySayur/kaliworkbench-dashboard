import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.allowed_scope import AllowedScope
from app.models.workspace import Workspace
from app.services.scope_validator import validate_target


@pytest_asyncio.fixture
async def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        ws = Workspace(name="ws", description=None)
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        yield session, ws.id
    await engine.dispose()


@pytest.mark.asyncio
async def test_deny_by_default_when_no_scopes(db_session):
    session, ws_id = db_session
    ok, reason = await validate_target(session, ws_id, "127.0.0.1")
    assert not ok
    assert "no allowlist" in reason


@pytest.mark.asyncio
async def test_ip_match(db_session):
    session, ws_id = db_session
    session.add(AllowedScope(workspace_id=ws_id, target_type="IP", value="127.0.0.1"))
    await session.commit()
    ok, _ = await validate_target(session, ws_id, "127.0.0.1")
    assert ok
    ok, _ = await validate_target(session, ws_id, "127.0.0.2")
    assert not ok


@pytest.mark.asyncio
async def test_cidr_contains_ip(db_session):
    session, ws_id = db_session
    session.add(AllowedScope(workspace_id=ws_id, target_type="CIDR", value="10.0.0.0/24"))
    await session.commit()
    ok, _ = await validate_target(session, ws_id, "10.0.0.5")
    assert ok
    ok, _ = await validate_target(session, ws_id, "10.0.1.5")
    assert not ok


@pytest.mark.asyncio
async def test_domain_match_exact_and_subdomain(db_session):
    session, ws_id = db_session
    session.add(AllowedScope(workspace_id=ws_id, target_type="Domain", value="example.local"))
    await session.commit()
    ok, _ = await validate_target(session, ws_id, "example.local")
    assert ok
    ok, _ = await validate_target(session, ws_id, "api.example.local")
    assert ok
    ok, _ = await validate_target(session, ws_id, "other.local")
    assert not ok


@pytest.mark.asyncio
async def test_cidr_target_must_be_subnet_of_allowed(db_session):
    session, ws_id = db_session
    session.add(AllowedScope(workspace_id=ws_id, target_type="CIDR", value="10.0.0.0/16"))
    await session.commit()
    ok, _ = await validate_target(session, ws_id, "10.0.1.0/24")
    assert ok
    ok, _ = await validate_target(session, ws_id, "10.1.0.0/24")
    assert not ok
