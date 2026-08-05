# Deployment

Four ways to run the pipeline outside a laptop, from zero-infra to production-shaped.
All of them run the same code path (`python -m revops run`); only the trigger and the
delivery differ.

| Path | Trigger | Delivery | Needs |
|---|---|---|---|
| [GitHub Actions](#github-actions-zero-infra) | Cron (Mon 07:00 UTC) or manual | Workflow artifact + optional Slack | Nothing (Slack webhook optional) |
| [Docker](#docker) | Whatever runs the container | Mounted `/reports` volume | Docker |
| [n8n](#n8n) | n8n schedule trigger | Slack channel | An n8n instance + Slack credentials |
| [Dust](#dust) | Conversation or Dust schedule | In-conversation / Slack | A Dust workspace |

## GitHub Actions (zero infra)

Already wired: [`.github/workflows/weekly-digest.yml`](../.github/workflows/weekly-digest.yml)
runs the pipeline every Monday, uploads the three reports as a build artifact, and posts
the digest to Slack when a `SLACK_WEBHOOK_URL` repository secret exists. Trigger it
manually from the Actions tab (`workflow_dispatch`) to test.

To enable Slack delivery: Slack workspace -> create an Incoming Webhook -> repo Settings
-> Secrets and variables -> Actions -> `SLACK_WEBHOOK_URL`.

## Docker

```bash
docker build -t revops .
docker run --rm -v "$PWD/reports:/reports" revops
# live mode
docker run --rm -v "$PWD/reports:/reports" -e ANTHROPIC_API_KEY revops run --out /reports --live
```

The image bundles the sample data; mount your own CSV/JSON and point at them with
`run --deals ... --calls ...` for real data.

## n8n

Import [`deploy/n8n/weekly-revops-digest.json`](../deploy/n8n/weekly-revops-digest.json)
(n8n -> Workflows -> Import from file). Three nodes: a Monday 07:00 schedule trigger, an
Execute Command node that runs the pipeline and cats the digest, and a Slack node posting
it. The sticky note in the workflow covers host requirements, live mode and error-workflow
wiring. If the n8n host cannot install Python packages, swap the command for the Docker
image above.

## Dust

The agent specs deploy as-is onto Dust with the sample files as datasources; the
walkthrough lives in [`deploy/dust/README.md`](../deploy/dust/README.md), including the
orchestration prompt that chains both analysis stages in one conversation.

## Which one to pick

- Showing the project to someone: GitHub Actions, it works from the repo alone.
- Wiring into an existing automation stack: n8n.
- Running against real exports on a schedule: Docker on any runner you already have.
- Demonstrating the agents as conversational co-workers: Dust.
