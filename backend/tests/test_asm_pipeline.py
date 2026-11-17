import pytest

from app.services.asm_pipeline import run_pipeline


@pytest.mark.asyncio
async def test_run_pipeline_single_command() -> None:
    results = await run_pipeline([["echo", "pipeline-ok"]], timeout=10)
    assert len(results) == 1
    assert results[0]["command"] == ["echo", "pipeline-ok"]
    assert "pipeline-ok" in results[0]["output"]
    assert results[0]["exit_code"] == 0


@pytest.mark.asyncio
async def test_run_pipeline_empty_commands_returns_empty() -> None:
    results = await run_pipeline([], timeout=10)
    assert results == []
