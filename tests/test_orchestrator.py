from pathlib import Path

from revops.orchestrator import load_deals, load_transcripts, run_pipeline
from revops.render import render_hygiene_report, render_risk_assessments

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def load_sample_run():
    deals = load_deals(SAMPLES / "dirty_crm_deals.csv")
    transcripts = load_transcripts(SAMPLES / "gong_call_transcripts.json")
    return deals, transcripts, run_pipeline(deals, transcripts)


def test_end_to_end_on_sample_data():
    deals, transcripts, result = load_sample_run()

    assert result.mode == "deterministic"
    assert result.hygiene_report.total_records == len(deals)
    assert len(result.clean_deals) == len(deals)  # nothing dropped
    assert result.hygiene_report.fixes, "sample data should trigger auto-fixes"
    assert result.hygiene_report.flags, "sample data should trigger flags"
    # every deal with a transcript gets assessed, every deal without one is reported
    transcripted_ids = {t.deal_id for t in transcripts}
    assert {a.deal_id for a in result.assessments} == transcripted_ids & {
        d.deal_id for d in deals
    }
    assert result.unassessed_deal_ids, "sample data leaves some deals without calls"
    assert not transcripted_ids & set(result.unassessed_deal_ids)
    assert "# Weekly Revenue Digest" in result.digest_markdown
    assert "High risk deals" in result.digest_markdown


def test_run_is_deterministic():
    _, _, first = load_sample_run()
    _, _, second = load_sample_run()
    assert first.digest_markdown == second.digest_markdown
    assert first.hygiene_report == second.hygiene_report


def test_transcripts_reference_real_deals():
    deals = load_deals(SAMPLES / "dirty_crm_deals.csv")
    transcripts = load_transcripts(SAMPLES / "gong_call_transcripts.json")
    deal_ids = {d.deal_id for d in deals}
    assert transcripts, "sample transcripts should not be empty"
    assert all(t.deal_id in deal_ids for t in transcripts)


def test_renderers_produce_markdown():
    _, _, result = load_sample_run()
    hygiene_md = render_hygiene_report(result)
    risk_md = render_risk_assessments(result)
    assert hygiene_md.startswith("# CRM Hygiene Report")
    assert "| Deal | Field | Old | New | Reason |" in hygiene_md
    assert risk_md.startswith("# Pipeline Risk Assessments")
    assert "**True Risk Level:**" in risk_md
