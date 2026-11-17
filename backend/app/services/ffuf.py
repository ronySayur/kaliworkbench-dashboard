from __future__ import annotations

import json
from typing import Any


def parse_ffuf_output(text: str) -> list[dict[str, Any]]:
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
        arr = data.get("Results") or data.get("results") or data.get("Findings") or data.get("findings") or []

    items = arr if isinstance(arr, list) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        status_code = item.get("status_code") or item.get("status") or item.get("@status")
        try:
            sc = int(status_code) if status_code is not None else 0
        except (TypeError, ValueError):
            sc = 0
        severity = "HIGH" if sc >= 500 else ("MEDIUM" if sc >= 400 else "INFO")
        url = str(item.get("url") or item.get("endpoint") or item.get("input") or "")
        title = f"Fuzz target responded with status {sc}" if sc else "Fuzz result captured"
        findings.append(
            {
                "severity": severity,
                "title": title,
                "evidence": item,
                "source": "ffuf",
            }
        )
    return findings
