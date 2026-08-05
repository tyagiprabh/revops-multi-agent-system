"""Command line entry point: python -m revops run"""

import argparse
import sys
from pathlib import Path

from .llm import ClaudeClient, api_key_available
from .orchestrator import load_deals, load_transcripts, run_pipeline
from .render import write_reports

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEALS = REPO_ROOT / "data" / "samples" / "dirty_crm_deals.csv"
DEFAULT_CALLS = REPO_ROOT / "data" / "samples" / "gong_call_transcripts.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="revops",
        description="Run the RevOps multi-agent pipeline on a CRM export + call transcripts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run hygiene -> pipeline analysis -> digest")
    run.add_argument("--deals", type=Path, default=DEFAULT_DEALS, help="CRM deals CSV")
    run.add_argument("--calls", type=Path, default=DEFAULT_CALLS, help="Transcripts JSON")
    run.add_argument(
        "--out", type=Path, default=REPO_ROOT / "reports" / "latest", help="Output directory"
    )
    run.add_argument(
        "--live",
        action="store_true",
        help="Use the Claude API for judgment steps (needs ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args(argv)

    client = None
    if args.live:
        if not api_key_available():
            print("--live requires ANTHROPIC_API_KEY to be set.", file=sys.stderr)
            return 1
        client = ClaudeClient()
        print(f"Live mode: judgment steps run on {client.model}.")
    else:
        print("Deterministic mode: no API key needed. Add --live for Claude-written analysis.")

    deals = load_deals(args.deals)
    transcripts = load_transcripts(args.calls)
    result = run_pipeline(deals, transcripts, client)
    write_reports(result, args.out)

    high = sum(1 for a in result.assessments if a.risk_level == "High")
    print(
        f"\n{result.hygiene_report.total_records} records -> "
        f"{len(result.hygiene_report.fixes)} auto-fixes, "
        f"{len(result.hygiene_report.flags)} flags, "
        f"{len(result.assessments)} deals risk-assessed ({high} High), "
        f"{len(result.unassessed_deal_ids)} without call data."
    )
    print(f"Reports written to {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
