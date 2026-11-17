from app.services.gitleaks import parse_gitleaks_output


def test_parse_empty_output_returns_empty() -> None:
    assert parse_gitleaks_output("") == []
    assert parse_gitleaks_output("\n\n") == []


def test_parse_gitleaks_json_array() -> None:
    text = """
    [
      {
        "RuleID": "generic-api-key",
        "Description": "Generic API key assignment",
        "Severity": "high",
        "Findings": [
          {
            "File": "src/config.py",
            "StartLine": 12,
            "EndLine": 12,
            "Excerpt": "api_key = 'abc'"
          }
        ]
      }
    ]
    """
    findings = parse_gitleaks_output(text)
    assert len(findings) == 1
    assert findings[0]["severity"] == "HIGH"
    assert findings[0]["title"] == "Generic API key assignment"
    assert findings[0]["source"] == "gitleaks"


def test_parse_gitleaks_jsonl() -> None:
    line1 = '{"RuleID": "aws-access-key", "Description": "AWS access key", "Severity": "critical"}'
    line2 = '{"RuleID": "generic-secret", "Description": "Generic secret", "Severity": "low"}'
    findings = parse_gitleaks_output(line1 + "\n" + line2)
    assert len(findings) == 2
    assert findings[0]["severity"] == "CRITICAL"
    assert findings[1]["severity"] == "LOW"
