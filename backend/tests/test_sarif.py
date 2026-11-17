from app.services.sarif import generate_sarif


def test_generate_sarif_empty_findings() -> None:
    sarif = generate_sarif([])
    assert sarif["version"] == "2.1.0"
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "KaliWorkbench"
    assert run["tool"]["driver"]["rules"] == []
    assert run["results"] == []


def test_generate_sarif_maps_severity_levels() -> None:
    findings = [
        {"severity": "CRITICAL", "title": "crit issue", "evidence": {"RuleID": "r-crit"}, "source": "nuclei"},
        {"severity": "MEDIUM", "title": "medium issue", "evidence": {"RuleID": "r-med"}, "source": "nuclei"},
        {"severity": "LOW", "title": "low issue", "evidence": None, "source": "gitleaks"},
    ]
    sarif = generate_sarif(findings)
    results = sarif["runs"][0]["results"]
    assert [r["level"] for r in results] == ["error", "warning", "note"]
    assert results[0]["ruleId"] == "r-crit"
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]
    assert {r["id"] for r in rules} == {"r-crit", "r-med", "gitleaks/low-issue"}


def test_generate_sarif_properties_not_required() -> None:
    sarif = generate_sarif([{"severity": "HIGH", "title": "t", "source": "ffuf"}])
    result = sarif["runs"][0]["results"][0]
    assert result["level"] == "error"
    assert result["message"]["text"] == "t"
