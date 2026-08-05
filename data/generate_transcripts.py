"""Generate synthetic sales-call transcripts linked to real CRM deals.

Reads data/samples/dirty_crm_deals.csv first so every transcript's deal_id
actually exists, then leaves ~25% of open deals without a call so the
Pipeline Analyst has genuine "unable to assess" cases.

Usage: python data/generate_transcripts.py
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(101)
random.seed(101)

OPEN_STAGES = ["Discovery", "Demo Scheduled", "Technical Validation", "Legal Review"]
COMPETITORS = ["AcmeCorp", "GlobalTech", "CloudSync"]
OBJECTIONS = [
    "We don't have the budget until Q3.",
    "Our current tool does this just fine.",
    "Implementation seems too complex for our small team.",
    "The security team needs to review your SOC2 first.",
]
BUYING_SIGNALS = [
    "Send over the contract and I'll get it to legal.",
    "This is exactly what we've been looking for.",
    "Can we get a pilot started next week?",
]


def generate_call_transcript(profile):
    """profile: 'negative' (objection/competitor), 'positive' (buying signal),
    or 'neutral' (no strong signal either way)."""
    transcript = [
        {"speaker": "Sales Rep",
         "text": f"Hi {fake.first_name()}, thanks for jumping on. How is your week going?"},
        {"speaker": "Prospect",
         "text": "Good, just busy. Let's dive right in, I only have 20 minutes."},
    ]
    exchanges = random.randint(3, 6)
    signal_at = random.randrange(exchanges)
    for i in range(exchanges):
        transcript.append({
            "speaker": "Sales Rep",
            "text": fake.sentence(nb_words=10, variable_nb_words=True) + "?",
        })
        if i == signal_at and profile == "negative":
            if random.random() < 0.35:
                response = (
                    f"Well, we are also looking at {random.choice(COMPETITORS)} right now. "
                    f"{fake.sentence()}"
                )
            else:
                response = random.choice(OBJECTIONS)
        elif i == signal_at and profile == "positive":
            response = random.choice(BUYING_SIGNALS)
        else:
            response = fake.paragraph(nb_sentences=2)
        transcript.append({"speaker": "Prospect", "text": response})
    return transcript


if __name__ == "__main__":
    samples = Path(__file__).parent / "samples"
    with open(samples / "dirty_crm_deals.csv", newline="", encoding="utf-8") as handle:
        deals = list(csv.DictReader(handle))

    open_deals = [d for d in deals if d["deal_stage"] in OPEN_STAGES]
    with_calls = random.sample(open_deals, k=int(len(open_deals) * 0.75))

    calls = []
    for deal in with_calls:
        call_date = datetime(2026, 8, 5) - timedelta(days=random.randint(1, 45))
        profile = random.choices(
            ["negative", "positive", "neutral"], weights=[30, 25, 45]
        )[0]
        calls.append({
            "call_id": fake.uuid4(),
            "deal_id": deal["deal_id"],
            "date": call_date.strftime("%Y-%m-%d"),
            "duration_minutes": random.randint(15, 45),
            "transcript": generate_call_transcript(profile),
        })

    out_path = samples / "gong_call_transcripts.json"
    out_path.write_text(json.dumps(calls, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(calls)} transcripts for {len(open_deals)} open deals "
        f"({len(open_deals) - len(with_calls)} left without call data) to {out_path}"
    )
