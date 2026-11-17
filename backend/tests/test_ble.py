import pytest

from app.services.ble_scanner import run_capture


@pytest.mark.asyncio
async def test_ble_inspect_runs_command() -> None:
    snapshot = await run_capture([["echo", "ble-ok"]], timeout=10)
    results = snapshot.get("results") if isinstance(snapshot, dict) else None
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["command"] == ["echo", "ble-ok"]
    assert "ble-ok" in results[0]["output"]
    assert results[0]["exit_code"] == 0
