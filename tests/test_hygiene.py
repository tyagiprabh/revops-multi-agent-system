from revops.agents.hygiene import run_hygiene


def test_lowercase_names_are_fixed_with_audit_trail(deal_factory):
    deal = deal_factory(first_name="jane", last_name="doe")
    cleaned, report = run_hygiene([deal])

    assert cleaned[0].first_name == "Jane"
    assert cleaned[0].last_name == "Doe"
    name_fixes = [f for f in report.fixes if f.field in ("first_name", "last_name")]
    assert len(name_fixes) == 2
    assert name_fixes[0].old_value == "jane"
    assert name_fixes[0].new_value == "Jane"
    assert name_fixes[0].reason  # audit trail requires a reason


def test_stray_whitespace_is_trimmed_before_other_checks(deal_factory):
    deal = deal_factory(
        first_name=" jane",
        company_name="Initech  ",
        email=" JANE.DOE@initech.com ".lower(),
    )
    cleaned, report = run_hygiene([deal])

    assert cleaned[0].first_name == "Jane"  # trimmed first, then case-fixed
    assert cleaned[0].company_name == "Initech"
    assert cleaned[0].email == "jane.doe@initech.com"
    whitespace_fixes = [f for f in report.fixes if "whitespace" in f.reason.lower()]
    assert {f.field for f in whitespace_fixes} == {"first_name", "company_name", "email"}
    assert all(f.new_value not in (f.old_value,) for f in whitespace_fixes)


def test_trimming_unmasks_duplicates(deal_factory):
    a = deal_factory(deal_id="DL-1", email="sam@initech.com")
    b = deal_factory(deal_id="DL-2", email=" sam@initech.com ")
    _, report = run_hygiene([a, b])
    dup_flags = [f for f in report.flags if f.flag_type == "possible_duplicate"]
    assert {f.deal_id for f in dup_flags} == {"DL-1", "DL-2"}


def test_country_variants_normalize_to_iso3(deal_factory):
    variants = [("US", "USA"), ("United States", "USA"), ("UK", "GBR"), ("France", "FRA")]
    for variant, expected in variants:
        cleaned, report = run_hygiene([deal_factory(country=variant)])
        assert cleaned[0].country == expected
    # Already canonical: nothing to fix
    _, report = run_hygiene([deal_factory(country="USA")])
    assert not [f for f in report.fixes if f.field == "country"]


def test_picklist_violation_is_flagged_not_guessed(deal_factory):
    deal = deal_factory(lead_source="Referral (Old)")
    cleaned, report = run_hygiene([deal])

    assert cleaned[0].lead_source == "Referral (Old)"  # untouched
    assert any(
        f.flag_type == "picklist_violation" and "Referral (Old)" in f.detail
        for f in report.flags
    )


def test_stale_open_deal_is_flagged(deal_factory):
    stale = deal_factory(deal_id="DL-1", deal_stage="Demo Scheduled", last_activity_days_ago=60)
    fresh = deal_factory(deal_id="DL-2", deal_stage="Demo Scheduled", last_activity_days_ago=10)
    closed = deal_factory(deal_id="DL-3", deal_stage="Closed Won", last_activity_days_ago=60)
    _, report = run_hygiene([stale, fresh, closed])

    stale_flags = [f for f in report.flags if f.flag_type == "stale_deal"]
    assert [f.deal_id for f in stale_flags] == ["DL-1"]


def test_duplicates_flagged_never_merged(deal_factory):
    a = deal_factory(deal_id="DL-1", email="sam@initech.com")
    b = deal_factory(deal_id="DL-2", email="sam@initech.com")
    cleaned, report = run_hygiene([a, b])

    assert len(cleaned) == 2  # NO SILENT DELETIONS
    dup_flags = [f for f in report.flags if f.flag_type == "possible_duplicate"]
    assert {f.deal_id for f in dup_flags} == {"DL-1", "DL-2"}
    assert all(f.confidence >= 0.9 for f in dup_flags)


def test_inputs_are_never_mutated(deal_factory):
    deal = deal_factory(first_name="jane", country="US")
    run_hygiene([deal])
    assert deal.first_name == "jane"
    assert deal.country == "US"
