from __future__ import annotations

import json
from typing import Any


def parse_nuclei_output(text: str) -> list[dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return []

    items: list[Any] = []
    try:
        data = json.loads(text)
        arr: Any = None
        if isinstance(data, list):
            arr = data
        elif isinstance(data, dict):
            arr = data.get("Findings") or data.get("findings") or data.get("Results") or data.get("results")
            if not isinstance(arr, list):
                arr = [data]
        items = arr if isinstance(arr, list) else []
    except Exception:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue

    findings: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        info = item.get("info") or {}
        severity_raw = str(info.get("severity") or item.get("severity") or "UNKNOWN").upper()
        title = str(info.get("name") or info.get("description") or item.get("name") or "Vulnerability detected")
        request = item.get("request") or {}
        url = str(request.get("url") or item.get("url") or item.get("host") or "") or ""
        findings.append(
            {
                "severity": severity_raw,
                "title": title,
                "evidence": item,
                "source": "nuclei",
            }
        )
    return findings
