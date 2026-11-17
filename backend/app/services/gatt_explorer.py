from __future__ import annotations

from typing import Any

from app.services.asm_pipeline import run_pipeline


async def run_capture(commands: list[list[str]], timeout: int) -> dict[str, Any]:
    results = await run_pipeline(commands, timeout)
    return {"results": results}
