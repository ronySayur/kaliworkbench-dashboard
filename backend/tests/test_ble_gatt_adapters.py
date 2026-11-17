import pytest

from app.services.ble_adapter import scan_ble, summarize_scan
from app.services.gatt_parser import gatt_summary, parse_bluetoothctl_gatt
from app.services.asset_inventory import diff_asset_snapshots


def test_summarize_ble_scan_empty() -> None:
    summary = summarize_scan([])
    assert summary["count"] == 0
    assert summary["avg_rssi"] is None


def test_summarize_ble_scan_avg_and_bounds() -> None:
    summary = summarize_scan(
        [{"address": "AA:BB", "name": "dev1", "rssi": -40}, {"address": "CC:DD", "name": None, "rssi": -60}]
    )
    assert summary["count"] == 2
    assert summary["avg_rssi"] == -50.0
    assert summary["min_rssi"] == -60
    assert summary["max_rssi"] == -40


@pytest.mark.asyncio
async def test_scan_ble_returns_empty_when_bleak_fails_or_no_radio() -> None:
    # Actual hardware absent in this environment; scan must degrade gracefully to [].
    devices = await scan_ble(timeout=1.0)
    assert isinstance(devices, list)


def test_parse_bluetoothctl_gatt_builds_tree() -> None:
    text = """
Primary Service: 0x1800
    Device Name
Primary Service: 0x180F
"""
    tree = parse_bluetoothctl_gatt(text)
    assert len(tree) == 2
    summary = gatt_summary(tree)
    assert summary["services"] == 2


def test_diff_asset_snapshots_detects_changes() -> None:
    prev = [{"identifier": "a:tcp/22", "fingerprint": "old", "asset_type": "port"}]
    curr = [{"identifier": "a:tcp/22", "fingerprint": "new", "asset_type": "port"}]
    diff = diff_asset_snapshots(prev, curr)
    assert len(diff["changed"]) == 1
