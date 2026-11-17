from __future__ import annotations

from typing import Any

from app.services.asm_pipeline import run_pipeline


async def run_snapshot(commands: list[list[str]], timeout: int) -> dict[str, Any]:
    results = await run_pipeline(commands, timeout)
    return {"results": results}


def diff_snapshots(snapshot_a: dict[str, Any], snapshot_b: dict[str, Any]) -> dict[str, Any]:
    results_a = snapshot_a.get("results") if isinstance(snapshot_a, dict) else None
    results_b = snapshot_b.get("results") if isinstance(snapshot_b, dict) else None
    list_a = results_a if isinstance(results_a, list) else []
    list_b = results_b if isinstance(results_b, list) else []
    differences: list[dict[str, Any]] = []
    for i in range(max(len(list_a), len(list_b))):
        a = list_a[i] if i < len(list_a) else None
        b = list_b[i] if i < len(list_b) else None
        if a is None or b is None:
            differences.append({"index": i, "status": "added" if b is not None else "removed"})
            continue
        if a.get("command") != b.get("command"):
            differences.append({"index": i, "status": "changed", "command": a.get("command")})
            continue
        if a.get("output") != b.get("output") or a.get("exit_code") != b.get("exit_code"):
            differences.append(
                {
                    "index": i,
                    "status": "changed",
                    "command": a.get("command"),
                    "source_exit": a.get("exit_code"),
                    "target_exit": b.get("exit_code"),
                }
            )
    return {"same": len(differences) == 0, "differences": differences}
