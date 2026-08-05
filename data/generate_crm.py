"""Generate a deliberately dirty CRM export (data/samples/dirty_crm_deals.csv).

The mess is intentional and matches what the CRM Hygiene agent must handle:
lowercase names, country variants, free email providers, picklist violations,
stale deals, and a handful of near-duplicate records.

Usage: python data/generate_crm.py [num_records]
"""

import csv
import random
import sys
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)  # keeps the data reproducible
random.seed(42)

VALID_SOURCES = ["Organic", "Outbound SDR", "Partner", "G2", "Events", "Direct"]
VALID_STAGES = [
    "Discovery", "Demo Scheduled", "Technical Validation",
    "Legal Review", "Closed Won", "Closed Lost",
]
VALID_SIZES = ["1-50", "51-200", "201-1000", "1000+"]
COUNTRY_VARIANTS = ["USA", "US", "United States", "GBR", "UK", "Great Britain", "FRA", "France"]

FIELDS = [
    "deal_id", "first_name", "last_name", "email", "company_name", "country",
    "lead_source", "deal_stage", "company_size", "arr_value", "last_activity_days_ago",
]


def make_record():
    first_name = fake.first_name()
    last_name = fake.last_name()
    company = fake.company()
    domain = company.lower().replace(" ", "").replace(",", "") + ".com"
    email = f"{first_name.lower()}.{last_name.lower()}@{domain}"

    # Formatting errors the agent should auto-fix
    if random.random() < 0.2:
        first_name = first_name.lower()
        last_name = last_name.lower()
    country = random.choice(COUNTRY_VARIANTS)

    # Hygiene issues the agent should flag, never fix silently
    if random.random() < 0.1:
        email = f"{first_name.lower()}{random.randint(1, 99)}@gmail.com"
    source = random.choice(VALID_SOURCES) if random.random() > 0.1 else "Referral (Old)"

    return {
        "deal_id": f"DL-{fake.unique.random_int(min=10000, max=99999)}",
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "company_name": company,
        "country": country,
        "lead_source": source,
        "deal_stage": random.choice(VALID_STAGES),
        "company_size": random.choice(VALID_SIZES),
        "arr_value": round(random.uniform(5000, 150000), 2),
        # Most deals have recent activity; an exponential tail keeps stale
        # deals and radio silence present without dominating the dataset.
        "last_activity_days_ago": min(90, int(random.expovariate(1 / 14)) + 1),
    }


def generate(num_records: int):
    records = [make_record() for _ in range(num_records)]

    # Inject near-duplicates (~3%): same contact re-entered under a new deal id,
    # sometimes with a different casing so only email or identity matching finds it.
    for source_record in random.sample(records, max(2, num_records // 33)):
        dup = dict(source_record)
        dup["deal_id"] = f"DL-{fake.unique.random_int(min=10000, max=99999)}"
        dup["deal_stage"] = random.choice(VALID_STAGES)
        dup["last_activity_days_ago"] = random.randint(1, 90)
        records.append(dup)

    random.shuffle(records)
    return records


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    out_path = Path(__file__).parent / "samples" / "dirty_crm_deals.csv"
    out_path.parent.mkdir(exist_ok=True)
    records = generate(count)
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records (incl. injected duplicates) to {out_path}")
