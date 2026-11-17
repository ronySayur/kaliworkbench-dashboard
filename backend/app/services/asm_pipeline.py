from __future__ import annotations

import asyncio
from typing import Any


async def run_pipeline(commands: list[list[str]], timeout: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for cmd in commands:
        if not cmd:
            continue
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
        output = ((out or b"").decode("utf-8", errors="replace")) + ((err or b"").decode("utf-8", errors="replace"))
        results.append(
            {
                "command": cmd,
                "output": output,
                "exit_code": proc.returncode,
            }
        )
    return results
