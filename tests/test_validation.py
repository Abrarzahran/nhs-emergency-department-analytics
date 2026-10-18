"""The validators must pass on the real data and must detect problems that are planted deliberately."""
import pandas as pd

from nhs_ed import validate


def test_real_data_has_no_failed_error_checks(clean):
    checks = validate.run_all(*clean)
    assert validate.failed_errors(checks) == [], [c.name for c in validate.failed_errors(checks)]


def test_org_rows_reconcile_exactly_to_published_totals(clean):
    check = validate.check_reconciles_to_published_totals(*clean)
    assert check.passed and "= 0" in check.detail


def test_twelve_months_april_2025_to_march_2026(clean):
    months = sorted(clean.org_month.month_start.unique())
    assert str(months[0].date()) == "2025-04-01" and str(months[-1].date()) == "2026-03-01" and len(months) == 12


def test_every_type1_organisation_reports_all_twelve_months(clean):
    assert validate.check_type1_orgs_complete(clean.org_month).passed


# Mutation tests: break the data on purpose and confirm that the check notices
def test_reconciliation_detects_a_single_changed_count(clean):
    org_month, totals = clean
    tampered = org_month.copy()
    tampered.loc[0, "t1_attendances"] += 1
    assert not validate.check_reconciles_to_published_totals(tampered, totals).passed


def test_detects_waits_over_4h_above_attendances(clean):
    tampered = clean.org_month.copy()
    tampered.loc[0, "t1_over_4hrs"] = tampered.loc[0, "t1_attendances"] + 1
    assert not validate.check_over4_not_above_attendances(tampered).passed


def test_detects_duplicate_rows(clean):
    tampered = pd.concat([clean.org_month, clean.org_month.iloc[[0]]], ignore_index=True)
    assert not validate.check_unique_keys(tampered).passed


def test_detects_negative_counts(clean):
    tampered = clean.org_month.copy()
    tampered.loc[0, "t2_attendances"] = -1
    assert not validate.check_no_nulls_or_negatives(tampered).passed


def test_detects_missing_month(clean):
    tampered = clean.org_month[clean.org_month.month_start != clean.org_month.month_start.min()]
    assert not validate.check_months(tampered).passed


def test_detects_type1_admissions_above_attendances(clean):
    tampered = clean.org_month.copy()
    tampered.loc[0, "t1_emergency_admissions"] = tampered.loc[0, "t1_attendances"] + tampered.loc[0, "t1_booked_attendances"] + 1
    assert not validate.check_type1_admissions_within_attendances(tampered).passed
