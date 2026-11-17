from __future__ import annotations

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KWB_", extra="ignore")

    app_name: str = "KaliWorkbench"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    allow_non_loopback: bool = False

    data_dir: Path = Path(__file__).resolve().parents[1] / "data"
    db_name: str = "kaliworkbench.db"

    session_token: str = secrets.token_urlsafe(32)
    log_batch_ms: int = 200
    log_ring_size: int = 2000
    job_timeout_default: int = 300
    job_cancel_grace_seconds: int = 3
    max_concurrent_jobs: int = 4

    @property
    def database_url(self) -> str:
        db_path = self.data_dir / self.db_name
        return f"sqlite+aiosqlite:///{db_path}"

    @property
    def loopback_only(self) -> bool:
        host = (self.host or "").strip().lower()
        return host in ("127.0.0.1", "localhost", "::1", "")


settings = Settings()
