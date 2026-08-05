"""Run a single deal through the Pipeline Analyst agent on Claude, standalone.

The smallest possible live demo: pick one deal, load its latest call
transcript, send both to Claude with agents/pipeline_analyst_agent.md as the
system prompt, and print the structured RiskAssessment that comes back.
The full pipeline equivalent is `python -m revops run --live`.

Setup:
    pip install -e ".[live]"
    export ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python run_claude_agent.py                 # first open deal with a call
    python run_claude_agent.py --deal DL-23069 # a specific deal
    python run_claude_agent.py --list          # show assessable deals
"""

import argparse
import sys
from pathlib import Path

from revops.agents.pipeline_analyst import assess_live
from revops.data_dictionary import OPEN_STAGES
from revops.llm import ClaudeClient, api_key_available
from revops.orchestrator import load_deals, load_transcripts

SAMPLES = Path(__file__).parent / "data" / "samples"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deal", help="deal_id to assess (default: first assessable deal)")
    parser.add_argument("--deals", type=Path, default=SAMPLES / "dirty_crm_deals.csv")
    parser.add_argument("--calls", type=Path, default=SAMPLES / "gong_call_transcripts.json")
    parser.add_argument("--list", action="store_true", help="list assessable deals and exit")
    args = parser.parse_args()

    deals = load_deals(args.deals)
    transcripts = load_transcripts(args.calls)
    latest_call = {}
    for call in transcripts:
        current = latest_call.get(call.deal_id)
        if current is None or call.date > current.date:
            latest_call[call.deal_id] = call
    assessable = [
        d for d in deals if d.deal_stage in OPEN_STAGES and d.deal_id in latest_call
    ]

    if args.list:
        for deal in assessable:
            print(f"{deal.deal_id}  {deal.deal_stage:<21} ${deal.arr_value:>10,.0f}")
        return 0

    if args.deal:
        matches = [d for d in assessable if d.deal_id == args.deal]
        if not matches:
            print(f"{args.deal} is not an open deal with a transcript. Try --list.",
                  file=sys.stderr)
            return 1
        deal = matches[0]
    else:
        deal = assessable[0]

    if not api_key_available():
        print("Set ANTHROPIC_API_KEY first (this script always runs live).", file=sys.stderr)
        return 1

    call = latest_call[deal.deal_id]
    client = ClaudeClient()
    print(
        f"Assessing {deal.deal_id} ({deal.deal_stage}, ${deal.arr_value:,.0f} ARR) "
        f"against its {call.date} call on {client.model}...\n"
    )
    assessment = assess_live(deal, call, client)
    print(assessment.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
