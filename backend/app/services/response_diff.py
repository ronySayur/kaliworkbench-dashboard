from __future__ import annotations

import asyncio
import json
from typing import Any


async def _run_command(cmd: list[str], timeout: int) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    out, err = await asyncio.wait_for(
        asyncio.gather(proc.stdout.read(), proc.stderr.read(), return_exceptions=True),
        timeout=timeout,
    )
    await asyncio.wait_for(proc.wait(), timeout=timeout)
    return ((out or b"").decode("utf-8", errors="replace")) + ((err or b"").decode("utf-8", errors="replace"))


async def run_pair(source_cmd: list[str], target_cmd: list[str], timeout: int) -> tuple[str, str]:
    src = await _run_command(source_cmd, timeout)
    tgt = await _run_command(target_cmd, timeout)
    return src, tgt


def _parse_json(text: str) -> Any:
    try:
        return json.loads(text or "")
    except Exception:
        return None


def diff_json(source: str, target: str) -> dict[str, Any]:
    a = _parse_json(source)
    b = _parse_json(target)
    if a is None or b is None:
        return {"same": False, "error": "source or target response was not valid JSON", "source": source, "target": target}
    diffs: list[dict[str, Any]] = []
    for key in sorted(set(a) | set(b)):
        if key not in a:
            diffs.append({"path": key, "status": "added", "value": b[key]})
        elif key not in b:
            diffs.append({"path": key, "status": "removed", "value": a[key]})
        elif a[key] != b[key]:
            diffs.append(
                {
                    "path": key,
                    "status": "changed",
                    "source_value": a[key],
                    "target_value": b[key],
                }
            )
    return {"same": len(diffs) == 0, "differences": diffs}
