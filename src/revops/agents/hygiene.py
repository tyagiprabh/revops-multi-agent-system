"""CRM Hygiene agent.

Implements agents/crm_hygiene_agent.md. This agent is deliberately 100%
deterministic: the spec's core guardrail is "only auto-fix when there is no
judgment involved", and a rules engine satisfies that better than a model.
No record is ever deleted, every change is logged as a FixAction.
"""


from ..data_dictionary import (
    COUNTRY_MAP,
    FREE_EMAIL_DOMAINS,
    OPEN_STAGES,
    STALE_AFTER_DAYS,
    VALID_SOURCES,
)
from ..schemas import Deal, FixAction, Flag, HygieneReport


def _fix_name_case(deal: Deal, field: str, fixes: list[FixAction]) -> None:
    value = getattr(deal, field)
    if value and value == value.lower():
        fixed = value.title()
        fixes.append(
            FixAction(
                deal_id=deal.deal_id,
                field=field,
                old_value=value,
                new_value=fixed,
                reason="Name stored fully lowercase; proper case is deterministic.",
            )
        )
        setattr(deal, field, fixed)


def _fix_country(deal: Deal, fixes: list[FixAction], flags: list[Flag]) -> None:
    canonical = COUNTRY_MAP.get(deal.country.strip().upper())
    if canonical is None:
        flags.append(
            Flag(
                deal_id=deal.deal_id,
                flag_type="picklist_violation",
                detail=f"country '{deal.country}' has no mapping in the data dictionary",
                confidence=1.0,
            )
        )
    elif canonical != deal.country:
        fixes.append(
            FixAction(
                deal_id=deal.deal_id,
                field="country",
                old_value=deal.country,
                new_value=canonical,
                reason="Data dictionary maps this variant to ISO alpha-3.",
            )
        )
        deal.country = canonical


def _flag_lead_source(deal: Deal, flags: list[Flag]) -> None:
    if deal.lead_source not in VALID_SOURCES:
        flags.append(
            Flag(
                deal_id=deal.deal_id,
                flag_type="picklist_violation",
                detail=(
                    f"lead_source '{deal.lead_source}' is not in the picklist; "
                    "mapping it to a valid source requires judgment"
                ),
                confidence=1.0,
            )
        )


def _flag_free_email(deal: Deal, flags: list[Flag]) -> None:
    domain = deal.email.rsplit("@", 1)[-1].lower()
    if domain in FREE_EMAIL_DOMAINS:
        flags.append(
            Flag(
                deal_id=deal.deal_id,
                flag_type="free_email_domain",
                detail=f"contact email uses free provider '{domain}'",
                confidence=0.9,
            )
        )


def _flag_stale(deal: Deal, flags: list[Flag]) -> None:
    if deal.deal_stage in OPEN_STAGES and deal.last_activity_days_ago > STALE_AFTER_DAYS:
        flags.append(
            Flag(
                deal_id=deal.deal_id,
                flag_type="stale_deal",
                detail=(
                    f"open deal ({deal.deal_stage}) with no activity for "
                    f"{deal.last_activity_days_ago} days; Deal Health set to At Risk"
                ),
                confidence=1.0,
            )
        )


def _flag_duplicates(deals: list[Deal], flags: list[Flag]) -> None:
    by_email: dict = {}
    by_identity: dict = {}
    for deal in deals:
        by_email.setdefault(deal.email.lower(), []).append(deal.deal_id)
        identity = (
            deal.first_name.lower(),
            deal.last_name.lower(),
            deal.company_name.lower(),
        )
        by_identity.setdefault(identity, []).append(deal.deal_id)

    seen_pairs = set()
    for email, ids in by_email.items():
        if len(ids) > 1:
            seen_pairs.add(frozenset(ids))
            for deal_id in ids:
                flags.append(
                    Flag(
                        deal_id=deal_id,
                        flag_type="possible_duplicate",
                        detail=f"shares email '{email}' with {sorted(set(ids) - {deal_id})}",
                        confidence=0.95,
                    )
                )
    for ids in by_identity.values():
        if len(ids) > 1 and frozenset(ids) not in seen_pairs:
            for deal_id in ids:
                flags.append(
                    Flag(
                        deal_id=deal_id,
                        flag_type="possible_duplicate",
                        detail=(
                            f"same contact and company as {sorted(set(ids) - {deal_id})} "
                            "(name + company match)"
                        ),
                        confidence=0.7,
                    )
                )


def run_hygiene(deals: list[Deal]) -> tuple[list[Deal], HygieneReport]:
    """Return cleaned copies of the deals plus the full audit report."""
    cleaned = [deal.model_copy(deep=True) for deal in deals]
    fixes: list[FixAction] = []
    flags: list[Flag] = []

    for deal in cleaned:
        _fix_name_case(deal, "first_name", fixes)
        _fix_name_case(deal, "last_name", fixes)
        _fix_country(deal, fixes, flags)
        _flag_lead_source(deal, flags)
        _flag_free_email(deal, flags)
        _flag_stale(deal, flags)

    _flag_duplicates(cleaned, flags)

    report = HygieneReport(total_records=len(cleaned), fixes=fixes, flags=flags)
    return cleaned, report
