from app.services.response_diff import diff_json


def test_diff_json_identical_responses() -> None:
    a = '{"user": {"id": 1, "role": "user"}, "ok": true}'
    b = '{"user": {"id": 1, "role": "user"}, "ok": true}'
    result = diff_json(a, b)
    assert result["same"] is True
    assert result["differences"] == []


def test_diff_json_changed_value() -> None:
    a = '{"user": {"id": 1, "role": "user"}, "ok": true}'
    b = '{"user": {"id": 1, "role": "admin"}, "ok": true}'
    result = diff_json(a, b)
    assert result["same"] is False
    assert len(result["differences"]) == 1
    assert result["differences"][0]["path"] == "user"
    assert result["differences"][0]["status"] == "changed"


def test_diff_json_added_and_removed_keys() -> None:
    a = '{"user": {"id": 1}}'
    b = '{"user": {"id": 1}, "extra": "x"}'
    result = diff_json(a, b)
    assert result["same"] is False
    assert any(d["status"] == "added" and d["path"] == "extra" for d in result["differences"])


def test_diff_json_invalid_json() -> None:
    result = diff_json("not-json", '{"ok": true}')
    assert result["same"] is False
    assert result.get("error")
