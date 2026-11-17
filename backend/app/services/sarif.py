from __future__ import annotations

import json
from typing import Any

_LEVEL_BY_SEVERITY = {
    "CRITICAL": "error",
    "HIGH": "error",
    "MEDIUM": "warning",
    "MODERATE": "warning",
    "LOW": "note",
    "INFO": "note",
    "UNKNOWN": "warning",
}


def _rule_id(finding: dict[str, Any]) -> str:
    evidence = finding.get("evidence") or {}
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except Exception:
            evidence = {}
    if isinstance(evidence, dict):
        rule_id = evidence.get("RuleID") or evidence.get("ruleId") or evidence.get("Rule") or evidence.get("@id")
        if rule_id:
            return str(rule_id)
    source = str(finding.get("source") or "finding")
    title = str(finding.get("title") or "untitled").lower().replace(" ", "-")[:64]
    return f"{source}/{title}"


def generate_sarif(findings: list[dict[str, Any]], tool_name: str = "KaliWorkbench") -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for finding in findings or []:
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity") or "UNKNOWN").upper()
        level = _LEVEL_BY_SEVERITY.get(severity, "warning")
        rule_id = _rule_id(finding)
        title = str(finding.get("title") or "Finding")

        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": title},
                "defaultConfiguration": {"level": level},
            }

        evidence = finding.get("evidence")
        if isinstance(evidence, (dict, list)):
            evidence_text = json.dumps(evidence, ensure_ascii=False)
        else:
            evidence_text = str(evidence or "")
        if len(evidence_text) > 2000:
            evidence_text = evidence_text[:2000] + "…"

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": title},
        }
        if evidence_text:
            result["properties"] = {"evidence": evidence_text, "severity": severity}
        results.append(result)

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }
