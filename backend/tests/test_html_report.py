from app.services.html_report import render_job_report_html


def test_html_report_renders_job_metadata_and_escapes_html() -> None:
    body = render_job_report_html(
        job_id=11,
        module="<nuclei>",
        status="succeeded",
        workspace_id=2,
        command_args='{"cmd": "echo <injected> &"}',
        started_at=None,
        finished_at=None,
        findings=[{"severity": "HIGH", "title": "<script>alert(1)</script>"}],
    )
    assert "<nuclei>" not in body
    assert "&lt;nuclei&gt;" in body
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body


def test_html_report_empty_findings_renders_empty_state() -> None:
    body = render_job_report_html(
        job_id=1,
        module="gitleaks",
        status="succeeded",
        workspace_id=1,
        command_args="{}",
        started_at=None,
        finished_at=None,
        findings=[],
    )
    assert "_No findings recorded" not in body  # markdown-style marker should not leak
    assert "No findings recorded for this job." in body
