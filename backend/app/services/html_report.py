from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def render_job_report_html(
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
    rows = "\n".join(
        f"<tr><td>{_esc(f.get('severity') or 'UNKNOWN')}</td><td>{_esc(f.get('title') or 'Finding')}</td></tr>"
        for f in findings
    )
    findings_block = (
        "<p><em>No findings recorded for this job.</em></p>"
        if not findings
        else f"<table><thead><tr><th>Severity</th><th>Title</th></tr></thead><tbody>\n{rows}\n</tbody></table>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>KaliWorkbench — Job #{_esc(job_id)} Report</title>
<style>
body {{ font-family: ui-sans-serif, system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; background:#0b1220; color:#e2e8f0; }}
h1 {{ color:#67e8f9; font-size:1.5rem; }}
table {{ width:100%; border-collapse: collapse; margin-top: 1rem; }}
th, td {{ border-bottom:1px solid #334155; text-align:left; padding:0.5rem; }}
thead {{ background:#1e293b; }}
pre {{ background:#0f172a; border:1px solid #334155; padding:0.75rem; overflow:auto; }}
</style>
</head>
<body>
<h1>KaliWorkbench — Job #{_esc(job_id)} Report</h1>
<ul>
  <li><strong>Workspace:</strong> {_esc(workspace_id)}</li>
  <li><strong>Module:</strong> {_esc(module)}</li>
  <li><strong>Status:</strong> {_esc(status)}</li>
  <li><strong>Started:</strong> {_esc(started_at or 'n/a')}</li>
  <li><strong>Finished:</strong> {_esc(finished_at or 'n/a')}</li>
  <li><strong>Generated:</strong> {_esc(datetime.now(timezone.utc).isoformat())}</li>
</ul>
<h2>Command</h2>
<pre>{_esc(command_args)}</pre>
<h2>Findings</h2>
{findings_block}
</body>
</html>
"""
