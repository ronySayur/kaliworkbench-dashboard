import pytest

from app.services.lan_tshark import run_capture


@pytest.mark.asyncio
async def test_lan_inspect_runs_command() -> None:
    snapshot = await run_capture([["echo", "lan-ok"]], timeout=10)
    results = snapshot.get("results") if isinstance(snapshot, dict) else None
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["command"] == ["echo", "lan-ok"]
    assert "lan-ok" in results[0]["output"]
    assert results[0]["exit_code"] == 0
