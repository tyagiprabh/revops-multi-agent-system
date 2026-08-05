"""Sequential orchestrator: Hygiene -> Pipeline Analyst -> Revenue Digest.

Each agent only sees typed inputs and produces typed outputs, so the chain is
easy to test in isolation and the digest can never quote a record the hygiene
pass did not approve.
"""

import csv
import json
from pathlib import Path
from typing import Optional

from .agents.digest import build_digest
from .agents.hygiene import run_hygiene
from .agents.pipeline_analyst import run_pipeline_analysis
from .llm import ClaudeClient
from .schemas import CallTranscript, Deal, RunResult


def load_deals(csv_path: Path) -> list[Deal]:
    with open(csv_path, newline="", encoding="utf-8") as handle:
        return [Deal(**row) for row in csv.DictReader(handle)]


def load_transcripts(json_path: Path) -> list[CallTranscript]:
    raw = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return [CallTranscript(**call) for call in raw]


def run_pipeline(
    deals: list[Deal],
    transcripts: list[CallTranscript],
    client: Optional[ClaudeClient] = None,
) -> RunResult:
    clean_deals, hygiene_report = run_hygiene(deals)
    assessments, unassessed = run_pipeline_analysis(clean_deals, transcripts, client)
    digest, summary = build_digest(
        clean_deals, hygiene_report, assessments, unassessed, client
    )
    return RunResult(
        hygiene_report=hygiene_report,
        clean_deals=clean_deals,
        assessments=assessments,
        unassessed_deal_ids=unassessed,
        digest_markdown=digest,
        mode="live" if client is not None else "deterministic",
        executive_summary=summary,
    )
