from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    endpoint_or_device: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_new_diff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job = relationship("Job", back_populates="findings")

    def to_dict(self) -> dict[str, Any]:
        try:
            evidence = json.loads(self.evidence_json) if self.evidence_json else None
        except Exception:
            evidence = None
        return {
            "id": self.id,
            "job_id": self.job_id,
            "severity": self.severity,
            "title": self.title,
            "endpoint_or_device": self.endpoint_or_device,
            "evidence": evidence,
            "is_new_diff": self.is_new_diff,
            "created_at": self.created_at,
        }
