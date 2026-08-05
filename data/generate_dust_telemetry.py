"""Generate synthetic AI-agent-platform telemetry (Dust-style workspace analytics).

This is the ops side of running an agent fleet: workspaces, seats, deployed
agents and per-invocation telemetry. The dataset feeds the usage-analytics
work on the roadmap (seat utilization, error rates, credit burn per model)
and is independent of the CRM pipeline demo.

Produces four files in data/samples/:
  dust_workspaces.csv   one row per customer workspace
  dust_users.csv        seats per workspace (Admin / Builder / Member)
  dust_agents.csv       deployed agents with model + connected tools
  dust_telemetry.json   per-invocation events over the last 30 days

Usage: python data/generate_dust_telemetry.py [workspaces] [events]
"""

import csv
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(7)
random.seed(7)

REFERENCE_DATE = datetime(2026, 8, 5)  # fixed so runs are reproducible

PLANS = {"Business": (1000, 4000), "Enterprise": (5000, 12000)}
WORKSPACE_STATUS = (["Active"] * 8) + ["At Risk", "Churned"]
SEAT_TYPES = ["Free (500 credits)", "Pro (8,000 credits)", "Max (40,000 credits)"]
MODELS = ["GPT-4o", "Claude 3.5 Sonnet", "Mistral Large", "Gemini 1.5 Pro"]
TOOLS = ["Zendesk", "GitHub", "Snowflake", "Salesforce", "Google Drive", "Notion", "Slack"]
AGENT_ROLES = [
    "Support Router", "Market Researcher", "HR Onboarding",
    "Code Reviewer", "Data Analyst", "Sales Prospector",
]
EVENT_STATUS = ["Success", "Tool Auth Error", "Rate Limited"]
EVENT_WEIGHTS = [85, 10, 5]


def make_workspaces(count):
    workspaces = []
    for _ in range(count):
        plan = random.choices(list(PLANS), weights=[75, 25])[0]
        low, high = PLANS[plan]
        workspaces.append({
            "workspace_id": f"WS-{fake.unique.random_int(min=1000, max=9999)}",
            "company_name": fake.company(),
            "plan": plan,
            "data_residency": random.choices(["US", "EU"], weights=[70, 30])[0],
            "mrr": round(random.uniform(low, high), 2),
            "status": random.choice(WORKSPACE_STATUS),
        })
    return workspaces


def make_users(workspaces):
    users = []
    for workspace in workspaces:
        seats = random.randint(15, 45)
        for i in range(seats):
            users.append({
                "user_id": f"USR-{fake.unique.random_int(min=10000, max=99999)}",
                "workspace_id": workspace["workspace_id"],
                "email": fake.email(),
                # exactly one Admin per workspace, then ~20% Builders
                "role": "Admin" if i == 0 else random.choices(
                    ["Builder", "Member"], weights=[20, 80])[0],
                "seat_type": random.choices(SEAT_TYPES, weights=[45, 35, 20])[0],
            })
    return users


def make_agents(workspaces, users):
    users_by_ws = {}
    for user in users:
        users_by_ws.setdefault(user["workspace_id"], []).append(user["user_id"])

    agents = []
    for workspace in workspaces:
        for _ in range(random.randint(3, 8)):
            agents.append({
                "agent_id": f"AGT-{fake.unique.random_int(min=10000, max=99999)}",
                "workspace_id": workspace["workspace_id"],
                "creator_user_id": random.choice(users_by_ws[workspace["workspace_id"]]),
                "agent_name": f"{random.choice(AGENT_ROLES)} - {fake.word().title()}",
                "model": random.choice(MODELS),
                "connected_tools": str(random.sample(TOOLS, k=random.randint(1, 3))),
            })
    return agents


def make_telemetry(users, agents, count):
    agents_by_ws = {}
    for agent in agents:
        agents_by_ws.setdefault(agent["workspace_id"], []).append(agent)

    events = []
    for _ in range(count):
        user = random.choice(users)
        agent = random.choice(agents_by_ws[user["workspace_id"]])
        status = random.choices(EVENT_STATUS, weights=EVENT_WEIGHTS)[0]
        moment = REFERENCE_DATE - timedelta(
            days=random.randint(0, 30),
            seconds=random.randint(0, 86_399),
            microseconds=random.randint(0, 999_999),
        )
        events.append({
            "event_id": fake.uuid4(),
            "timestamp": moment.isoformat(),
            "workspace_id": user["workspace_id"],
            "user_id": user["user_id"],
            "agent_id": agent["agent_id"],
            "agent_model_used": agent["model"],
            "status": status,
            "credits_consumed": random.randint(10, 150) if status == "Success" else 0,
        })
    events.sort(key=lambda e: e["timestamp"])
    return events


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    num_workspaces = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    num_events = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    samples = Path(__file__).parent / "samples"
    samples.mkdir(exist_ok=True)

    workspaces = make_workspaces(num_workspaces)
    users = make_users(workspaces)
    agents = make_agents(workspaces, users)
    events = make_telemetry(users, agents, num_events)

    write_csv(samples / "dust_workspaces.csv", workspaces)
    write_csv(samples / "dust_users.csv", users)
    write_csv(samples / "dust_agents.csv", agents)
    (samples / "dust_telemetry.json").write_text(
        json.dumps(events, indent=2), encoding="utf-8"
    )
    print(
        f"Wrote {len(workspaces)} workspaces, {len(users)} users, "
        f"{len(agents)} agents, {len(events)} telemetry events to {samples}/"
    )
