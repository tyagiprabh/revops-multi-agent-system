"""Typed contracts passed between agents.

Every agent consumes and produces one of these models, so the orchestrator
never passes loose dicts around and the live LLM mode can validate Claude's
output against the exact same schema.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Deal(BaseModel):
    deal_id: str
    first_name: str
    last_name: str
    email: str
    company_name: str
    country: str
    lead_source: str
    deal_stage: str
    company_size: str
    arr_value: float
    last_activity_days_ago: int


class TranscriptTurn(BaseModel):
    speaker: Literal["Sales Rep", "Prospect"]
    text: str


class CallTranscript(BaseModel):
    call_id: str
    deal_id: str
    date: str
    duration_minutes: int
    transcript: list[TranscriptTurn]

    def prospect_lines(self) -> list[str]:
        return [t.text for t in self.transcript if t.speaker == "Prospect"]


class FixAction(BaseModel):
    """One deterministic auto-fix, logged so a human can roll it back."""

    deal_id: str
    field: str
    old_value: str
    new_value: str
    reason: str


FlagType = Literal[
    "possible_duplicate",
    "stale_deal",
    "free_email_domain",
    "picklist_violation",
]


class Flag(BaseModel):
    """Anything that needs human judgment. Flags are never auto-applied."""

    deal_id: str
    flag_type: FlagType
    detail: str
    confidence: float = Field(ge=0.0, le=1.0)


class HygieneReport(BaseModel):
    total_records: int
    fixes: list[FixAction]
    flags: list[Flag]

    def flag_counts(self) -> dict:
        counts: dict = {}
        for flag in self.flags:
            counts[flag.flag_type] = counts.get(flag.flag_type, 0) + 1
        return counts


class RiskAssessment(BaseModel):
    """Strict output schema from agents/pipeline_analyst_agent.md."""

    deal_id: str
    crm_stage: str
    risk_level: Literal["High", "Medium", "Low"]
    justification: list[str] = Field(
        description="Evidence bullets. Quote the prospect directly where possible."
    )
    recommended_action: str = Field(
        description="One sentence instruction for the Sales Manager."
    )


class RunResult(BaseModel):
    hygiene_report: HygieneReport
    clean_deals: list[Deal]
    assessments: list[RiskAssessment]
    unassessed_deal_ids: list[str]
    digest_markdown: str
    mode: Literal["deterministic", "live"]
    executive_summary: Optional[str] = None
