import pytest

from revops.schemas import CallTranscript, Deal, TranscriptTurn


def make_deal(**overrides) -> Deal:
    base = dict(
        deal_id="DL-10001",
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@initech.com",
        company_name="Initech",
        country="USA",
        lead_source="Organic",
        deal_stage="Discovery",
        company_size="51-200",
        arr_value=42000.0,
        last_activity_days_ago=5,
    )
    base.update(overrides)
    return Deal(**base)


def make_call(deal_id: str, prospect_lines, date: str = "2026-08-01") -> CallTranscript:
    turns = [TranscriptTurn(speaker="Sales Rep", text="How are things going?")]
    for line in prospect_lines:
        turns.append(TranscriptTurn(speaker="Prospect", text=line))
    return CallTranscript(
        call_id="c-" + deal_id,
        deal_id=deal_id,
        date=date,
        duration_minutes=30,
        transcript=turns,
    )


@pytest.fixture
def deal_factory():
    return make_deal


@pytest.fixture
def call_factory():
    return make_call
