# Data Dictionary

Canonical field definitions for the CRM deals dataset. The CRM Hygiene agent validates
every record against this dictionary: deterministic mismatches are auto-fixed with an
audit trail, everything requiring judgment is flagged for human review.

The same values live in code at [`src/revops/data_dictionary.py`](../src/revops/data_dictionary.py),
which is the machine-readable source of truth for the pipeline.

## `dirty_crm_deals.csv`

| Field | Type | Canonical values / format | Notes |
|---|---|---|---|
| `deal_id` | string | `DL-#####` | Primary key, unique per deal |
| `first_name` | string | Proper case | Auto-fixed if fully lowercase |
| `last_name` | string | Proper case | Auto-fixed if fully lowercase |
| `email` | string | `first.last@companydomain` | Free-mail domains (gmail, yahoo, outlook, hotmail) are flagged, never rewritten |
| `company_name` | string | Free text | Used for duplicate matching together with contact name |
| `country` | string | ISO 3166-1 alpha-3: `USA`, `GBR`, `FRA` | Variants like `US`, `United States`, `UK`, `Great Britain`, `France` are auto-normalized |
| `lead_source` | enum | `Organic`, `Outbound SDR`, `Partner`, `G2`, `Events`, `Direct` | Values outside the picklist (e.g. legacy `Referral (Old)`) are flagged, not guessed |
| `deal_stage` | enum | `Discovery`, `Demo Scheduled`, `Technical Validation`, `Legal Review`, `Closed Won`, `Closed Lost` | First four stages count as open pipeline |
| `company_size` | enum | `1-50`, `51-200`, `201-1000`, `1000+` | Employee bands |
| `arr_value` | float | USD, 2 decimals | Annual recurring revenue of the deal |
| `last_activity_days_ago` | int | 0 to 90 | Days since last logged call, email or meeting |

## Derived rules

| Rule | Threshold | Owner |
|---|---|---|
| Stale deal | Open stage and no activity for more than 45 days | CRM Hygiene agent flags, deal owner acts |
| Radio silence (risk signal) | No activity for 30+ days | Pipeline Analyst agent, feeds High risk rating |
| Duplicate suspicion | Same email, or same contact name + company | CRM Hygiene agent flags with confidence score, never auto-merges |

## `gong_call_transcripts.json`

| Field | Type | Notes |
|---|---|---|
| `call_id` | string (UUID) | Unique per call |
| `deal_id` | string | Foreign key into `dirty_crm_deals.csv` |
| `date` | string | ISO date `YYYY-MM-DD` |
| `duration_minutes` | int | 15 to 45 |
| `transcript` | array | Ordered turns of `{"speaker": "Sales Rep" \| "Prospect", "text": "..."}` |
