from __future__ import annotations

import json
import re
from typing import Any

_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret|authorization|password|passphrase|token|secret|basic\s+[a-z0-9+/=._-]+)"
)


def _flatten_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
        try:
            parsed = json.loads(obj)
            out.extend(_flatten_strings(parsed))
        except Exception:
            pass
    elif isinstance(obj, dict):
        for value in obj.values():
            out.extend(_flatten_strings(value))
    elif isinstance(obj, list):
        for value in obj:
            out.extend(_flatten_strings(value))
    elif obj is not None:
        out.append(str(obj))
    return out


def parse_tshark_output(text: str) -> list[dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return []

    candidates: list[str] = []
    try:
        data = json.loads(text)
        candidates.extend(_flatten_strings(data))
    except Exception:
        candidates.append(text)
        candidates.extend(line for line in text.splitlines() if line.strip())

    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        for match in _SECRET_RE.finditer(candidate):
            snippet = candidate[max(0, match.start() - 40): match.end() + 80].strip()
            fingerprint = snippet[:120]
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            findings.append(
                {
                    "severity": "HIGH",
                    "title": "Cleartext credential-like value detected in packet capture",
                    "evidence": {"snippet": snippet},
                    "source": "tshark",
                }
            )
    return findings
