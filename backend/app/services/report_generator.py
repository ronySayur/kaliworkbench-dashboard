from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_report(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_severity: dict[str, int] = {}
    for f in findings or []:
        if not isinstance(f, dict):
            continue
        severity = str(f.get("severity") or f.get("Severity") or "UNKNOWN").upper()
        by_severity[severity] = by_severity.get(severity, 0) + 1
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(findings or []),
        "by_severity": by_severity,
    }
