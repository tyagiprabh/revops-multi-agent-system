"""Revenue Digest agent.

Implements agents/revenue_digest_agent.md. All numbers are computed in code
(the spec forbids the model from inventing figures); in live mode Claude only
writes the executive summary on top of the computed digest.
"""

from pathlib import Path
from typing import Optional

from ..data_dictionary import OPEN_STAGES
from ..llm import ClaudeClient
from ..schemas import Deal, HygieneReport, RiskAssessment

_SPEC_PATH = Path(__file__).resolve().parents[3] / "agents" / "revenue_digest_agent.md"

TOP_RISKS = 5


def build_digest(
    deals: list[Deal],
    hygiene: HygieneReport,
    assessments: list[RiskAssessment],
    unassessed: list[str],
    client: Optional[ClaudeClient] = None,
) -> tuple[str, Optional[str]]:
    """Return (digest_markdown, executive_summary_or_None)."""
    by_id = {deal.deal_id: deal for deal in deals}
    open_deals = [d for d in deals if d.deal_stage in OPEN_STAGES]
    open_arr = sum(d.arr_value for d in open_deals)

    stage_lines = []
    for stage in OPEN_STAGES:
        stage_deals = [d for d in open_deals if d.deal_stage == stage]
        stage_lines.append(
            f"| {stage} | {len(stage_deals)} | ${sum(d.arr_value for d in stage_deals):,.0f} |"
        )

    high = [a for a in assessments if a.risk_level == "High"]
    high_arr = sum(by_id[a.deal_id].arr_value for a in high if a.deal_id in by_id)
    top_high = sorted(
        (a for a in high if a.deal_id in by_id),
        key=lambda a: by_id[a.deal_id].arr_value,
        reverse=True,
    )[:TOP_RISKS]

    risk_lines = []
    for assessment in top_high:
        deal = by_id[assessment.deal_id]
        reason = assessment.justification[0] if assessment.justification else "see assessment"
        risk_lines.append(
            f"| {assessment.deal_id} | ${deal.arr_value:,.0f} | {assessment.crm_stage} | {reason} |"
        )

    flag_counts = hygiene.flag_counts()
    flag_lines = [
        f"- {count} x `{flag_type}`"
        for flag_type, count in sorted(flag_counts.items(), key=lambda kv: -kv[1])
    ]

    sections = [
        "# Weekly Revenue Digest",
        "",
        "## Pipeline snapshot",
        "",
        f"Open pipeline: **${open_arr:,.0f}** across **{len(open_deals)}** deals.",
        "",
        "| Stage | Deals | ARR |",
        "|---|---|---|",
        *stage_lines,
        "",
        "## Risk callout",
        "",
        (
            f"**${high_arr:,.0f}** of ARR sits in **{len(high)}** High risk deals "
            f"({len(assessments)} deals assessed, {len(unassessed)} without call data)."
        ),
        "",
        "| Deal | ARR | CRM stage | Why it is at risk |",
        "|---|---|---|---|",
        *risk_lines,
        "",
        "## Hygiene status",
        "",
        (
            f"{len(hygiene.fixes)} deterministic fixes applied with an audit trail; "
            f"{len(hygiene.flags)} flags waiting for human review:"
        ),
        *flag_lines,
        "",
        "## Recommended actions",
        "",
        (
            f"1. **Sales Manager**: review the {len(top_high)} deals in the risk table "
            "and re-qualify before the next forecast call."
        ),
        (
            "2. **Deal Owners**: every stale deal flagged above gets an activity logged "
            "this week or moves to Closed Lost."
        ),
        (
            "3. **RevOps**: resolve the duplicate flags before they pollute "
            "the next attribution report."
        ),
    ]
    digest = "\n".join(sections)

    summary: Optional[str] = None
    if client is not None:
        system = _SPEC_PATH.read_text(encoding="utf-8")
        summary = client.write(
            system=system,
            prompt=(
                "Here is the fully computed weekly digest. Write the two-sentence "
                "executive summary that should sit at the very top. Use only numbers "
                f"that appear below.\n\n{digest}"
            ),
        )
        digest = f"# Weekly Revenue Digest\n\n> {summary}\n" + digest.split(
            "# Weekly Revenue Digest", 1
        )[1]

    return digest, summary
