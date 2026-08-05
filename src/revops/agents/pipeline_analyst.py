"""Pipeline Analyst agent.

Implements agents/pipeline_analyst_agent.md: cross-reference what the CRM
claims about a deal with what the prospect actually said on the last call,
then score risk with the spec's rubric.

Two interchangeable engines produce the same RiskAssessment schema:

* deterministic  - keyword signal extraction + the rubric, runs offline.
                   Used for the demo, the tests and CI.
* live (Claude)  - the agent spec becomes the system prompt and Claude
                   returns a structured RiskAssessment. Used when an
                   ANTHROPIC_API_KEY is available.
"""

from typing import Optional

from ..data_dictionary import LATE_STAGES, OPEN_STAGES, SILENCE_AFTER_DAYS
from ..llm import ClaudeClient
from ..paths import repo_file
from ..schemas import CallTranscript, Deal, RiskAssessment

BUDGET_MARKERS = ["budget", "too expensive", "can't afford", "cost is"]
STALL_MARKERS = [
    "check back",
    "next quarter",
    "too complex",
    "current tool does this",
    "needs to review",
    "not a priority",
]
COMPETITORS = ["AcmeCorp", "GlobalTech", "CloudSync"]
BUYING_MARKERS = [
    "send over the contract",
    "send the contract",
    "exactly what we've been looking for",
    "get a pilot started",
    "start a pilot",
]

_SPEC_PATH = repo_file("agents", "pipeline_analyst_agent.md")


def _find_quotes(lines: list[str], markers: list[str]) -> list[str]:
    quotes = []
    for line in lines:
        lowered = line.lower()
        if any(marker.lower() in lowered for marker in markers):
            quotes.append(line.strip())
    return quotes


def assess_deterministic(deal: Deal, call: CallTranscript) -> RiskAssessment:
    lines = call.prospect_lines()
    budget = _find_quotes(lines, BUDGET_MARKERS)
    stalls = _find_quotes(lines, STALL_MARKERS)
    competitors = _find_quotes(lines, COMPETITORS)
    buying = _find_quotes(lines, BUYING_MARKERS)
    silent = deal.last_activity_days_ago >= SILENCE_AFTER_DAYS

    justification: list[str] = []
    for quote in (budget + stalls + competitors)[:2]:
        justification.append(f'Prospect said: "{quote}"')

    if budget or stalls or competitors or silent:
        risk = "High"
        if silent:
            justification.append(
                f"No logged activity for {deal.last_activity_days_ago} days (radio silence)."
            )
        blocker = "budget objection" if budget else (
            "competitor in play" if competitors else (
                "stall tactics" if stalls else "radio silence"))
        justification.append(
            f"CRM stage '{deal.deal_stage}' is not supported by the conversation: {blocker}."
        )
        action = (
            "Escalate to the Sales Manager: re-qualify before any further "
            f"stage movement; address the {blocker} head-on."
        )
    elif buying:
        risk = "Low"
        justification.append(f'Prospect said: "{buying[0]}"')
        justification.append("Explicit buying signal with no blocker raised on the call.")
        action = "Keep momentum: confirm the agreed next step in writing within 24 hours."
    else:
        risk = "Medium"
        justification.append("No explicit next step was agreed on the last call.")
        if deal.deal_stage in LATE_STAGES:
            justification.append(
                f"CRM stage '{deal.deal_stage}' is ahead of what the conversation supports."
            )
            action = "Ask the Deal Owner to secure a concrete next step before keeping this stage."
        else:
            action = "Ask the Deal Owner to book the next meeting with an explicit agenda."

    return RiskAssessment(
        deal_id=deal.deal_id,
        crm_stage=deal.deal_stage,
        risk_level=risk,
        justification=justification,
        recommended_action=action,
    )


def assess_live(deal: Deal, call: CallTranscript, client: ClaudeClient) -> RiskAssessment:
    system = _SPEC_PATH.read_text(encoding="utf-8")
    dialogue = "\n".join(f"{t.speaker}: {t.text}" for t in call.transcript)
    prompt = (
        f"CRM record:\n"
        f"- Deal ID: {deal.deal_id}\n"
        f"- Stage: {deal.deal_stage}\n"
        f"- ARR value: ${deal.arr_value:,.0f}\n"
        f"- Days since last activity: {deal.last_activity_days_ago}\n\n"
        f"Most recent call transcript ({call.date}, {call.duration_minutes} min):\n"
        f"{dialogue}\n\n"
        f"Evaluate this deal."
    )
    return client.parse(system=system, prompt=prompt, schema=RiskAssessment)


def run_pipeline_analysis(
    deals: list[Deal],
    transcripts: list[CallTranscript],
    client: Optional[ClaudeClient] = None,
) -> tuple[list[RiskAssessment], list[str]]:
    """Assess every open deal that has a transcript; report the ones that don't.

    Closed deals are out of scope. Per the spec: an open deal without
    conversational data is never scored, it is returned in the unassessed
    list instead ("Unable to assess").
    """
    latest_call: dict = {}
    for call in transcripts:
        existing = latest_call.get(call.deal_id)
        if existing is None or call.date > existing.date:
            latest_call[call.deal_id] = call

    assessments: list[RiskAssessment] = []
    unassessed: list[str] = []
    for deal in (d for d in deals if d.deal_stage in OPEN_STAGES):
        call = latest_call.get(deal.deal_id)
        if call is None:
            unassessed.append(deal.deal_id)
        elif client is not None:
            assessments.append(assess_live(deal, call, client))
        else:
            assessments.append(assess_deterministic(deal, call))
    return assessments, unassessed
