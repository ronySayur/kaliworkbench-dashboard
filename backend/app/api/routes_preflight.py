from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.utils.preflight import check_tool

router = APIRouter(prefix="/api", tags=["preflight"], dependencies=[Depends(verify_token)])

_KNOWN_TOOLS: dict[str, list[str]] = {
    "gitleaks": ["version"],
    "ffuf": ["-V"],
    "nuclei": ["-version"],
    "nmap": ["--version"],
    "subfinder": ["-version"],
    "httpx": ["-version"],
    "gowitness": ["version"],
    "tshark": ["-v"],
    "bettercap": ["-version"],
    "airodump-ng": ["--help"],
    "kismet": ["--version"],
    "bluetoothctl": ["--version"],
    "btmon": ["--version"],
    "bleak": ["--version"],
}


@router.get("/preflight")
async def preflight_checks() -> dict:
    results = {name: check_tool(name, args) for name, args in _KNOWN_TOOLS.items()}
    return {
        "tools": [
            {"name": t.name, "path": t.path, "version": t.version, "ok": t.ok}
            for t in results.values()
        ]
    }
