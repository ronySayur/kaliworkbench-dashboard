from app.services.report_generator import generate_report


def test_report_counts_by_severity() -> None:
    findings = [
        {"severity": "high", "title": "x"},
        {"severity": "HIGH", "title": "y"},
        {"severity": "low", "title": "z"},
        {"title": "no-severity"},
    ]
    report = generate_report(findings)
    assert report["total"] == 4
    assert report["by_severity"]["HIGH"] == 2
    assert report["by_severity"]["LOW"] == 1
    assert report["by_severity"]["UNKNOWN"] == 1
    assert "generated_at" in report


def test_report_empty_findings() -> None:
    report = generate_report([])
    assert report["total"] == 0
    assert report["by_severity"] == {}


def test_report_ignores_non_dict_entries() -> None:
    report = generate_report([{"severity": "critical"}, "junk", None])
    assert report["total"] == 3
    assert report["by_severity"]["CRITICAL"] == 1
