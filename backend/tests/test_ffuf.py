from app.services.ffuf import parse_ffuf_output


def test_parse_ffuf_empty_output_returns_empty() -> None:
    assert parse_ffuf_output("") == []


def test_parse_ffuf_json_array_high_and_low() -> None:
    text = """
    [
      {"status": 200, "url": "http://127.0.0.1:8080/admin", "status_code": 200},
      {"status": 500, "url": "http://127.0.0.1:8080/secret", "status_code": 500}
    ]
    """
    findings = parse_ffuf_output(text)
    assert len(findings) == 2
    assert findings[0]["severity"] == "INFO"
    assert findings[1]["severity"] == "HIGH"


def test_parse_ffuf_jsonl() -> None:
    line1 = '{"status": 404, "url": "http://127.0.0.1:8080/missing", "status_code": 404}'
    line2 = '{"status": 403, "url": "http://127.0.0.1:8080/forbidden", "status_code": 403}'
    findings = parse_ffuf_output(line1 + "\n" + line2)
    assert len(findings) == 2
    assert findings[0]["severity"] == "MEDIUM"
    assert findings[1]["severity"] == "MEDIUM"
