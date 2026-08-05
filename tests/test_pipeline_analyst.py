from revops.agents.pipeline_analyst import run_pipeline_analysis


def test_budget_objection_scores_high_with_quote(deal_factory, call_factory):
    deal = deal_factory(deal_id="DL-1", deal_stage="Demo Scheduled")
    call = call_factory("DL-1", ["We don't have the budget until Q3."])
    assessments, _ = run_pipeline_analysis([deal], [call])

    assert assessments[0].risk_level == "High"
    assert any("budget" in j.lower() for j in assessments[0].justification)
    assert any('"' in j for j in assessments[0].justification)  # direct quote included


def test_competitor_mention_scores_high(deal_factory, call_factory):
    deal = deal_factory(deal_id="DL-1")
    call = call_factory("DL-1", ["Well, we are also looking at AcmeCorp right now."])
    assessments, _ = run_pipeline_analysis([deal], [call])
    assert assessments[0].risk_level == "High"


def test_radio_silence_scores_high_even_without_objection(deal_factory, call_factory):
    deal = deal_factory(deal_id="DL-1", last_activity_days_ago=35)
    call = call_factory("DL-1", ["Thanks, that was a useful overview of the roadmap."])
    assessments, _ = run_pipeline_analysis([deal], [call])
    assert assessments[0].risk_level == "High"


def test_buying_signal_scores_low(deal_factory, call_factory):
    deal = deal_factory(deal_id="DL-1", last_activity_days_ago=3)
    call = call_factory("DL-1", ["Send over the contract and I'll get it to legal."])
    assessments, _ = run_pipeline_analysis([deal], [call])

    assert assessments[0].risk_level == "Low"
    assert "24 hours" in assessments[0].recommended_action


def test_late_stage_without_signal_scores_medium(deal_factory, call_factory):
    deal = deal_factory(deal_id="DL-1", deal_stage="Legal Review", last_activity_days_ago=5)
    call = call_factory("DL-1", ["Thanks, that was a useful overview of the roadmap."])
    assessments, _ = run_pipeline_analysis([deal], [call])

    assert assessments[0].risk_level == "Medium"
    assert any("ahead of" in j for j in assessments[0].justification)


def test_deal_without_transcript_is_unassessed(deal_factory, call_factory):
    with_call = deal_factory(deal_id="DL-1")
    without_call = deal_factory(deal_id="DL-2")
    call = call_factory("DL-1", ["Can we get a pilot started next week?"])
    assessments, unassessed = run_pipeline_analysis([with_call, without_call], [call])

    assert [a.deal_id for a in assessments] == ["DL-1"]
    assert unassessed == ["DL-2"]


def test_most_recent_call_wins(deal_factory, call_factory):
    deal = deal_factory(deal_id="DL-1", last_activity_days_ago=2)
    old = call_factory("DL-1", ["We don't have the budget until Q3."], date="2026-07-01")
    contract = "Send over the contract and I'll get it to legal."
    new = call_factory("DL-1", [contract], date="2026-08-01")
    assessments, _ = run_pipeline_analysis([deal], [old, new])
    assert assessments[0].risk_level == "Low"
