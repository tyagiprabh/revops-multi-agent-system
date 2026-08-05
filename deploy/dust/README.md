# Deploying the agents on Dust

The specs in [`agents/`](../../agents) are written to run unchanged as
[Dust](https://dust.tt) agents. This guide recreates the pipeline there, with the CSV and
JSON samples as datasources instead of the local orchestrator.

## 1. Create the datasources

In your Dust workspace, create a folder (e.g. `revops-data`) and upload:

| File | Used by |
|---|---|
| `data/samples/dirty_crm_deals.csv` | CRM Hygiene, Pipeline Analyst |
| `data/samples/gong_call_transcripts.json` | Pipeline Analyst |
| `docs/data_dictionary.md` | CRM Hygiene |

Regenerate larger versions first with the scripts in [`data/`](../../data) if you want a
heavier demo.

## 2. Create the three agents

For each agent: **New agent**, paste the full spec as Instructions, then attach tools.

| Dust agent | Instructions from | Tools to attach |
|---|---|---|
| `@crm-janitor` | `agents/crm_hygiene_agent.md` | Search on `revops-data` (the specs' Tool Routing section maps `get_crm_deals` and `read_data_dictionary` to it) |
| `@pipeline-analyst` | `agents/pipeline_analyst_agent.md` | Search on `revops-data` |
| `@revenue-digest` | `agents/revenue_digest_agent.md` | None required (it compresses the other agents' outputs); optionally Slack for delivery |

Model: pick the strongest reasoning model available in your workspace. The specs already
carry tool routing, a think-before-acting phase and search budgets, so no extra
instructions are needed.

## 3. Run the pipeline as a conversation

The orchestration prompt below chains the two analysis stages in one conversation
(the same flow `src/revops/orchestrator.py` runs in code):

```text
Stage 1: As @crm-janitor, audit the first 50 rows of dirty_crm_deals.csv against
data_dictionary.md. Report auto-fixes (casing, ISO countries, whitespace) with an
audit trail, and flag duplicates, free-mail contacts, picklist violations and
stale deals (>45 days) for human review. Never delete or rewrite data.

Stage 2: As @pipeline-analyst, match gong_call_transcripts.json to those deal IDs
and score each open deal High/Medium/Low using direct prospect quotes. If a deal
has no transcript, say "No transcript available for this deal."

Finish: As @revenue-digest, compress both outputs into the weekly digest format.
```

## 4. What to expect vs the local pipeline

- The local rules engine is deterministic; a Dust agent reading the CSV applies judgment.
  Expect it to catch things keyword rules miss (e.g. a "budget" keyword inside filler
  text is not a real budget objection) and to be slower per deal.
- Guardrails live in the spec text on Dust, in code + tests locally. That difference is
  the point of the repo's "deterministic core, LLM judgment layer" design.
