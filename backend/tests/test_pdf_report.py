from app.services.pdf_report import render_job_report_pdf
from app.services.nmap import parse_nmap_xml
from app.services.airodump import parse_airodump_csv, detect_rogue_aps


def test_pdf_report_renders_non_empty_pdf() -> None:
    body = render_job_report_pdf(
        job_id=5,
        module="nuclei",
        status="succeeded",
        workspace_id=7,
        command_args='{"command": ["nuclei", "-u", "http://x"]}',
        started_at=None,
        finished_at=None,
        findings=[{"severity": "high", "title": "RCE in login", "evidence": {"template": "cve-x"}}],
    )
    assert isinstance(body, (bytes, bytearray))
    assert len(body) > 200
    assert body[:5] == b"%PDF-"


def test_pdf_report_without_findings_still_renders() -> None:
    body = render_job_report_pdf(
        job_id=1,
        module="gitleaks",
        status="succeeded",
        workspace_id=1,
        command_args="{}",
        started_at=None,
        finished_at=None,
        findings=[],
    )
    assert body[:5] == b"%PDF-"
