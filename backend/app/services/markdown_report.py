from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def _md_escape(text: Any) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ")


def render_job_report_markdown(
    *,
    job_id: int,
    module: str,
    status: str,
    workspace_id: int,
    command_args: str,
    started_at: str | None,
    finished_at: str | None,
    findings: list[dict[str, Any]],
) -> str:
    lines = [
        f"# KaliWorkbench — Job #{job_id} Report",
        "",
        f"- Workspace: {workspace_id}",
        f"- Module: {_md_escape(module)}",
        f"- Status: {_md_escape(status)}",
        f"- Started: {started_at or 'n/a'}",
        f"- Finished: {finished_at or 'n/a'}",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Command",
        "",
        "```json",
        command_args or "n/a",
        "```",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("_No findings recorded for this job._")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Severity | Title |")
    lines.append("| --- | --- |")
    for f in findings:
        sev = _md_escape(f.get("severity") or "UNKNOWN")
        title = _md_escape(f.get("title") or "Finding")
        lines.append(f"| {sev} | {title} |")
    lines.append("")
    for i, f in enumerate(findings, start=1):
        lines.append(f"### Finding {i} — {_md_escape(f.get('severity') or 'UNKNOWN')}")
        lines.append("")
        lines.append(f"**{_md_escape(f.get('title') or 'Finding')}**")
        lines.append("")
        evidence = f.get("evidence")
        if evidence:
            rendered = json.dumps(evidence, ensure_ascii=False, indent=2) if isinstance(evidence, (dict, list)) else str(evidence)
            lines.append("```json")
            lines.append(rendered[:4000])
            lines.append("```")
            lines.append("")
    return "\n".join(lines)
