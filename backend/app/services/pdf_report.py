from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _pdf_safe(text: Any) -> str:
    return str(text if text is not None else "").encode("latin-1", errors="replace").decode("latin-1")


def _wrap(text: str, width: int) -> list[str]:
    return [text[i : i + width] for i in range(0, max(len(text), 1), width)]


def render_job_report_pdf(
    *,
    job_id: int,
    module: str,
    status: str,
    workspace_id: int,
    command_args: str,
    started_at: str | None,
    finished_at: str | None,
    findings: list[dict[str, Any]],
) -> bytes:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    def h2(text: str) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, f"KaliWorkbench - Job #{job_id} Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated: {datetime.now(timezone.utc).isoformat()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    h2("Metadata")
    pdf.set_font("Helvetica", "", 10)
    for label, value in [
        ("Workspace", workspace_id),
        ("Module", module),
        ("Status", status),
        ("Started", started_at or "n/a"),
        ("Finished", finished_at or "n/a"),
    ]:
        pdf.set_x(pdf.l_margin)
        pdf.cell(50, 6, f"{label}:")
        pdf.cell(0, 6, _pdf_safe(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    h2("Command")
    pdf.set_font("Courier", "", 8)
    for raw in (command_args or "").splitlines()[:20] or ["n/a"]:
        for chunk in _wrap(_pdf_safe(raw), 95):
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 4, chunk, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    h2(f"Findings ({len(findings or [])})")
    if not findings:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "No findings recorded for this job.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for i, finding in enumerate(findings or [], start=1):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(pdf.l_margin)
        pdf.cell(
            0,
            6,
            _pdf_safe(
                f"{i}. [{str(finding.get('severity') or 'UNKNOWN').upper()}] {finding.get('title') or 'Finding'}"
            ),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        evidence = finding.get("evidence")
        if evidence:
            import json as _json

            rendered = (
                _json.dumps(evidence, ensure_ascii=False)
                if isinstance(evidence, (dict, list))
                else str(evidence)
            )
            pdf.set_font("Courier", "", 7)
            for chunk in _wrap(_pdf_safe(rendered[:1500]), 110):
                pdf.set_x(pdf.l_margin)
                pdf.cell(0, 4, chunk, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    return bytes(pdf.output())
