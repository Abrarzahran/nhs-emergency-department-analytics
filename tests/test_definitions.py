"""Checks derived from NHS England's "A&E Attendances and Emergency Admissions Monthly Return Definitions" v5.0 (Aug 2020).
Section references (A1i, A3, B1iv ...) are to that document; see docs/DEFINITIONS_CROSSWALK.md."""
from nhs_ed import validate
from nhs_ed.config import ORG_LEVEL_COLUMNS, TYPE_COLUMNS


def test_type1_departments_sit_under_three_character_trust_codes(clean):
    # Definitions, "A&E Activity": data submitted against the 3-character provider code for NHS trusts.
    assert validate.check_type1_providers_use_trust_codes(clean.org_month).passed


def test_other_ae_department_is_the_third_type_in_every_group():
    # A1iii / A1vi / A2iii / B1iii: "Other A&E department" = Type 3 / Urgent Treatment Centres.
    assert set(TYPE_COLUMNS) == {"Type 1", "Type 2", "Other"}
    assert TYPE_COLUMNS["Other"]["attendances"].endswith("Other A&E Department")


def test_booked_and_unbooked_series_are_internally_consistent(clean):
    # A1i-iii exclude booked appointments (A1iv-vi report them separately), so each over-4h count must be bounded by its own series.
    om = clean.org_month
    for k in ("t1", "t2", "oth"):
        assert (om[f"{k}_over_4hrs"] <= om[f"{k}_attendances"]).all()
        assert (om[f"{k}_booked_over_4hrs"] <= om[f"{k}_booked_attendances"]).all()


def test_decision_to_admit_bands_are_org_level_not_by_type():
    # A3 / A4 are single counts of waits for emergency admission via A&E (not split by Type 1/2/3).
    assert {"dta_4_to_12h", "dta_12h_plus"} <= set(ORG_LEVEL_COLUMNS)


def test_orgs_with_admissions_but_no_ae_activity_exist_as_the_definitions_allow(clean):
    # Definitions: all providers admitting >= 40 emergency patients a month report, even with no A&E (B1iv "other" admissions).
    om = clean.org_month
    by_org = om.groupby("org_code")[["t1_attendances", "t2_attendances", "oth_attendances", "t1_booked_attendances",
                                     "t2_booked_attendances", "oth_booked_attendances", "other_emergency_admissions"]].sum()
    no_ae = by_org[by_org.iloc[:, :6].sum(axis=1) == 0]
    assert len(no_ae) > 0 and (no_ae.other_emergency_admissions.sum() > 0)


def test_warning_checks_are_reported_not_fatal(clean):
    checks = validate.run_all(*clean)
    assert validate.failed_errors(checks) == []
    assert any("200 or fewer attendances" in c.name for c in checks)
