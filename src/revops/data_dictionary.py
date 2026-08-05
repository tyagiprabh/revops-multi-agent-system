"""Canonical picklists and normalization rules.

Machine-readable twin of docs/data_dictionary.md. The hygiene agent only
auto-fixes what this module can resolve deterministically; everything else
becomes a flag for human review.
"""

VALID_SOURCES = ["Organic", "Outbound SDR", "Partner", "G2", "Events", "Direct"]

VALID_STAGES = [
    "Discovery",
    "Demo Scheduled",
    "Technical Validation",
    "Legal Review",
    "Closed Won",
    "Closed Lost",
]

OPEN_STAGES = ["Discovery", "Demo Scheduled", "Technical Validation", "Legal Review"]

# Stages late enough that we expect an explicit buying signal on the last call.
LATE_STAGES = ["Technical Validation", "Legal Review"]

VALID_SIZES = ["1-50", "51-200", "201-1000", "1000+"]

# Country variants -> ISO 3166-1 alpha-3. Only mappings listed here are
# considered deterministic; anything else is left untouched and flagged.
COUNTRY_MAP = {
    "US": "USA",
    "USA": "USA",
    "UNITED STATES": "USA",
    "UK": "GBR",
    "GBR": "GBR",
    "GREAT BRITAIN": "GBR",
    "UNITED KINGDOM": "GBR",
    "FRANCE": "FRA",
    "FRA": "FRA",
}

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}

STALE_AFTER_DAYS = 45      # hygiene: open deal with no activity -> "At Risk"
SILENCE_AFTER_DAYS = 30    # analyst: radio silence counts as a High risk signal
