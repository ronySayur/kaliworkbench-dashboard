from __future__ import annotations

import re

_DOMAIN_RE = re.compile(r"^[a-z0-9._-]+\.[a-z]{2,}$")


def parse_subfinder_output(text: str) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()
    for raw in (text or "").splitlines():
        line = raw.strip().lower().rstrip(".")
        if not line or line.startswith("#"):
            continue
        if line.startswith("*."):
            line = line[2:]
        if not _DOMAIN_RE.match(line):
            continue
        if line not in seen:
            seen.add(line)
            results.append(line)
    return results
