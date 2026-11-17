from app.services.nuclei import parse_nuclei_output


def test_parse_nuclei_empty_output_returns_empty() -> None:
    assert parse_nuclei_output("") == []


def test_parse_nuclei_json_array() -> None:
    text = """
    [
      {
        "info": {"name": "CVE-2024-1234", "severity": "critical"},
        "request": {"url": "http://127.0.0.1:8080/vulnerable"}
      }
    ]
    """
    findings = parse_nuclei_output(text)
    assert len(findings) == 1
    assert findings[0]["severity"] == "CRITICAL"
    assert findings[0]["title"] == "CVE-2024-1234"
    assert findings[0]["source"] == "nuclei"


def test_parse_nuclei_jsonl_missing_info_defaults() -> None:
    line = '{"@id": "abc", "info": {"severity": "low"}, "request": {"url": "http://127.0.0.1:8080/x"}}'
    findings = parse_nuclei_output(line)
    assert len(findings) == 1
    assert findings[0]["severity"] == "LOW"
