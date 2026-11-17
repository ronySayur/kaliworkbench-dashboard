from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class ToolCheck:
    name: str
    path: str | None
    version: str | None
    ok: bool


def check_tool(name: str, version_args: list[str] | None = None) -> ToolCheck:
    path = shutil.which(name)
    if not path:
        return ToolCheck(name=name, path=None, version=None, ok=False)
    version = None
    if version_args:
        try:
            proc = subprocess.run(
                [name, *version_args],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            out = (proc.stdout or proc.stderr or "").strip()
            version = out.splitlines()[0] if out else None
        except Exception:
            version = None
    return ToolCheck(name=name, path=path, version=version, ok=True)
