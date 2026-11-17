from app.services.markdown_report import render_job_report_markdown


def test_markdown_report_no_findings_includes_command() -> None:
    body = render_job_report_markdown(
        job_id=7,
        module="gitleaks",
        status="succeeded",
        workspace_id=3,
        command_args='{"command": ["cat", "x"]}',
        started_at=None,
        finished_at=None,
        findings=[],
    )
    assert "# KaliWorkbench — Job #7 Report" in body
    assert "- Module: gitleaks" in body
    assert "_No findings recorded for this job._" in body
    assert "cat" in body


def test_markdown_report_renders_findings_and_escapes_titles() -> None:
    body = render_job_report_markdown(
        job_id=1,
        module="nuclei",
        status="failed",
        workspace_id=1,
        command_args="{}",
        started_at="2026-11-17T00:00:00Z",
        finished_at=None,
        findings=[
            {"severity": "HIGH", "title": "pipe | char and\nnewline", "evidence": {"RuleID": "r-1"}},
        ],
    )
    assert "| HIGH | pipe \\| char and newline |" in body
    assert "r-1" in body
