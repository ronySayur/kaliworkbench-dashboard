from __future__ import annotations

import json
from typing import Any


def parse_gitleaks_output(text: str) -> list[dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return []

    data: Any = None
    try:
        data = json.loads(text)
    except Exception:
        items: list[Any] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
        data = items

    findings: list[dict[str, Any]] = []
    arr: Any = None
    if isinstance(data, list):
        arr = data
    elif isinstance(data, dict):
        arr = data.get("Findings") or data.get("findings") or data.get("Results") or []

    items = arr if isinstance(arr, list) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        severity_raw = str(item.get("Severity") or item.get("severity") or "UNKNOWN").upper()
        title_raw = str(item.get("Description") or item.get("description") or item.get("RuleID") or "Secret detected")
        findings.append(
            {
                "severity": severity_raw,
                "title": title_raw,
                "evidence": item,
                "source": "gitleaks",
            }
        )
    return findings
