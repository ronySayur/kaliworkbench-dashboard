from app.services.asset_snapshot import diff_snapshots


def test_diff_snapshots_identical() -> None:
    a = {"results": [{"command": ["echo", "x"], "output": "x\n", "exit_code": 0}]}
    b = {"results": [{"command": ["echo", "x"], "output": "x\n", "exit_code": 0}]}
    result = diff_snapshots(a, b)
    assert result["same"] is True
    assert result["differences"] == []


def test_diff_snapshots_changed() -> None:
    a = {"results": [{"command": ["echo", "x"], "output": "x\n", "exit_code": 0}]}
    b = {"results": [{"command": ["echo", "x"], "output": "y\n", "exit_code": 0}]}
    result = diff_snapshots(a, b)
    assert result["same"] is False
    assert len(result["differences"]) == 1


def test_diff_snapshots_missing_result() -> None:
    a = {"results": [{"command": ["echo", "x"], "output": "x\n", "exit_code": 0}]}
    b = {"results": []}
    result = diff_snapshots(a, b)
    assert result["same"] is False
    assert result["differences"][0]["status"] == "removed"
