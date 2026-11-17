from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes_asm_pipeline import router as asm_pipeline_router
from app.api.routes_asm_snapshot import router as asm_snapshot_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_ble import router as ble_router
from app.api.routes_gatt import router as gatt_router
from app.api.routes_lan import router as lan_router
from app.api.routes_preflight import router as preflight_router
from app.api.routes_asm_assets import router as asm_assets_router
from app.api.routes_ble_gatt import router as ble_gatt_router
from app.api.routes_report import router as report_router
from app.api.routes_rf import router as rf_router
from app.api.routes_response_diff import router as response_diff_router
from app.api.routes_scopes import router as scopes_router
from app.api.routes_workspaces import router as workspaces_router
from app.api.routes_ws import router as ws_router
from app.config import settings
from app.db.engine import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.loopback_only and not settings.allow_non_loopback:
        raise RuntimeError(
            f"Refusing to bind {settings.app_name} to non-loopback host {settings.host}. "
            "The HTTP surface has no user/authorization model yet — set KWB_ALLOW_NON_LOOPBACK=true "
            "or bind 127.0.0.1. See README Security notes."
        )
    await init_db()
    print("=" * 60)
    print(f"{settings.app_name} backend starting")
    print(f"Bind: http://{settings.host}:{settings.port}")
    if not settings.loopback_only:
        print("WARNING: non-loopback bind — only expose to trusted networks.")
    print(f"Session token: {settings.session_token}")
    print("Use Authorization: Bearer <token> for API requests")
    print("Use ?token=<token> for WebSocket connections")
    print("=" * 60)
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspaces_router)
app.include_router(scopes_router)
app.include_router(jobs_router)
app.include_router(response_diff_router)
app.include_router(asm_pipeline_router)
app.include_router(asm_snapshot_router)
app.include_router(asm_assets_router)
app.include_router(rf_router)
app.include_router(ble_gatt_router)
app.include_router(lan_router)
app.include_router(ble_router)
app.include_router(gatt_router)
app.include_router(report_router)
app.include_router(preflight_router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    wal_mode = None
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("PRAGMA journal_mode"))
            row = result.first()
            if row:
                wal_mode = str(row[0])
    except Exception:
        wal_mode = "unknown"
    return {"status": "ok", "app": settings.app_name, "journal_mode": wal_mode}
