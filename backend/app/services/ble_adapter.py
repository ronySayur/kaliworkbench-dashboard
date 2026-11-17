from __future__ import annotations

import asyncio
import statistics
from typing import Any


async def scan_ble(timeout: float = 5.0) -> list[dict[str, Any]]:
    """Live BLE scan via bleak. Returns [] when Bluetooth/adapter is unavailable."""
    try:
        from bleak import BleakScanner
    except Exception:
        return []
    devices: list[dict[str, Any]] = []
    try:
        discovered = await asyncio.wait_for(BleakScanner.discover(timeout=timeout), timeout=timeout + 2.0)
    except Exception:
        return []
    for device in discovered:
        rssi = getattr(device, "rssi", None)
        devices.append(
            {
                "address": getattr(device, "address", None),
                "name": getattr(device, "name", None),
                "rssi": rssi,
                "details": str(getattr(device, "details", "") or ""),
            }
        )
    return devices


def summarize_scan(devices: list[dict[str, Any]]) -> dict[str, Any]:
    rss = [d["rssi"] for d in devices if isinstance(d.get("rssi"), (int, float))]
    return {
        "count": len(devices),
        "avg_rssi": round(statistics.fmean(rss), 1) if rss else None,
        "min_rssi": min(rss) if rss else None,
        "max_rssi": max(rss) if rss else None,
    }
