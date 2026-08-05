"""Render run artifacts to markdown files."""

from pathlib import Path

from .schemas import RunResult


def render_hygiene_report(result: RunResult) -> str:
    report = result.hygiene_report
    lines = [
        "# CRM Hygiene Report",
        "",
        f"Records processed: **{report.total_records}** | "
        f"auto-fixes: **{len(report.fixes)}** | flags for review: **{len(report.flags)}**",
        "",
        "## Auto-fixes (with audit trail)",
        "",
        "| Deal | Field | Old | New | Reason |",
        "|---|---|---|---|---|",
    ]
    for fix in report.fixes:
        lines.append(
            f"| {fix.deal_id} | {fix.field} | {fix.old_value} | {fix.new_value} | {fix.reason} |"
        )
    lines += [
        "",
        "## Flags (human review queue)",
        "",
        "| Deal | Type | Confidence | Detail |",
        "|---|---|---|---|",
    ]
    for flag in report.flags:
        lines.append(
            f"| {flag.deal_id} | {flag.flag_type} | {flag.confidence:.0%} | {flag.detail} |"
        )
    return "\n".join(lines)


def render_risk_assessments(result: RunResult) -> str:
    lines = ["# Pipeline Risk Assessments", ""]
    order = {"High": 0, "Medium": 1, "Low": 2}
    for assessment in sorted(result.assessments, key=lambda a: order[a.risk_level]):
        lines += [
            f"## {assessment.deal_id}",
            "",
            f"**CRM Stage:** {assessment.crm_stage} | **True Risk Level:** {assessment.risk_level}",
            "",
            "**Risk Justification:**",
        ]
        lines += [f"- {bullet}" for bullet in assessment.justification]
        lines += ["", f"**Recommended Action:** {assessment.recommended_action}", ""]
    if result.unassessed_deal_ids:
        lines += [
            "## Unable to assess",
            "",
            "No conversational data available for: "
            + ", ".join(result.unassessed_deal_ids),
        ]
    return "\n".join(lines)


def write_reports(result: RunResult, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hygiene_report.md").write_text(
        render_hygiene_report(result), encoding="utf-8"
    )
    (out_dir / "risk_assessments.md").write_text(
        render_risk_assessments(result), encoding="utf-8"
    )
    (out_dir / "weekly_digest.md").write_text(result.digest_markdown, encoding="utf-8")
