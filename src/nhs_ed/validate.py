"""Data validation. Each check returns a Check(name, passed, severity, detail).

severity "error"   -> the data is wrong/unusable; the build stops.
severity "warning" -> unusual but plausible; reported, never silently "fixed".
"""
from dataclasses import dataclass

import pandas as pd

from .config import AE_TYPES, CLEAN_NUMERIC_COLUMNS, EXPECTED_MONTHS, FIRST_MONTH, LAST_MONTH, TYPE_KEY


@dataclass
class Check:
    name: str
    passed: bool
    severity: str  # "error" | "warning"
    detail: str


def check_months(org_month: pd.DataFrame) -> Check:
    expected = pd.date_range(FIRST_MONTH, LAST_MONTH, freq="MS")
    found = sorted(org_month["month_start"].unique())
    ok = list(expected) == list(found) and len(found) == EXPECTED_MONTHS
    return Check("12 contiguous months, Apr 2025 - Mar 2026", ok, "error", f"found {len(found)} months")


def check_unique_keys(org_month: pd.DataFrame) -> Check:
    dups = int(org_month.duplicated(["org_code", "month_start"]).sum())
    return Check("No duplicate (org_code, month) rows", dups == 0, "error", f"{dups} duplicates")


def check_no_nulls_or_negatives(org_month: pd.DataFrame) -> Check:
    nulls = int(org_month[CLEAN_NUMERIC_COLUMNS].isna().sum().sum())
    negs = int((org_month[CLEAN_NUMERIC_COLUMNS] < 0).sum().sum())
    return Check("No nulls or negative counts", nulls == 0 and negs == 0, "error", f"{nulls} nulls, {negs} negatives")


def check_one_total_per_month(totals: pd.DataFrame) -> Check:
    ok = len(totals) == EXPECTED_MONTHS and totals["month_start"].is_unique
    return Check("Exactly one published TOTAL row per month", ok, "error", f"{len(totals)} total rows")


def check_reconciles_to_published_totals(org_month: pd.DataFrame, totals: pd.DataFrame) -> Check:
    """The organisation rows must add up to NHS England's own TOTAL row, cell by cell."""
    ours = org_month.groupby("month_start")[CLEAN_NUMERIC_COLUMNS].sum()
    theirs = totals.set_index("month_start")[CLEAN_NUMERIC_COLUMNS]
    diff = (ours - theirs.loc[ours.index]).abs()
    worst = int(diff.to_numpy().max())
    return Check("Organisation rows sum to published TOTAL (all 18 columns, all months)", worst == 0, "error", f"largest absolute difference = {worst}")


def check_over4_not_above_attendances(org_month: pd.DataFrame) -> Check:
    bad = 0
    for key in TYPE_KEY.values():
        bad += int((org_month[f"{key}_over_4hrs"] > org_month[f"{key}_attendances"]).sum())
        bad += int((org_month[f"{key}_booked_over_4hrs"] > org_month[f"{key}_booked_attendances"]).sum())
    return Check("Waits over 4h never exceed attendances (all types, booked and unbooked)", bad == 0, "error", f"{bad} violations")


def check_type1_admissions_within_attendances(org_month: pd.DataFrame) -> Check:
    bad = int((org_month["t1_emergency_admissions"] > org_month["t1_attendances"] + org_month["t1_booked_attendances"]).sum())
    return Check("Type 1 emergency admissions never exceed Type 1 attendances", bad == 0, "error", f"{bad} violations")


def check_region_stable(org_month: pd.DataFrame) -> Check:
    n = int((org_month.groupby("org_code")["region"].nunique() > 1).sum())
    return Check("Each organisation stays in one region", n == 0, "error", f"{n} organisations changed region")


def check_type1_orgs_complete(org_month: pd.DataFrame) -> Check:
    t1 = org_month[org_month["t1_attendances"] > 0].groupby("org_code")["month_start"].nunique()
    incomplete = int((t1 < EXPECTED_MONTHS).sum())
    return Check("Every organisation with Type 1 activity reports in all 12 months", incomplete == 0, "warning", f"{incomplete} of {len(t1)} incomplete")


def warn_renamed_orgs(org_month: pd.DataFrame) -> Check:
    n = int((org_month.groupby("org_code")["org_name"].nunique() > 1).sum())
    return Check("Organisations whose name changed during the year (handled by keying on org_code)", True, "warning", f"{n} organisations renamed")


def warn_dta_12h_above_4_12h(org_month: pd.DataFrame) -> Check:
    n = int((org_month["dta_12h_plus"] > org_month["dta_4_to_12h"]).sum())
    return Check("Org-months where over-12h DTA waits exceed 4-12h DTA waits (kept as published)", True, "warning", f"{n} org-months")


def check_type1_providers_use_trust_codes(org_month: pd.DataFrame) -> Check:
    """NHS England definitions v5.0: data are submitted against the 3-character provider code for NHS trusts
    (other organisation types use other codes). Every Type 1 department should therefore sit under a 3-character code."""
    codes = org_month.loc[org_month["t1_attendances"] > 0, "org_code"].unique()
    bad = [c for c in codes if len(c) != 3]
    return Check("Every organisation reporting Type 1 activity has a 3-character trust code (definitions v5.0)", not bad, "warning",
                 f"{len(bad)} of {len(codes)} not 3 characters")


def warn_series_averaging_200_or_less(org_month: pd.DataFrame) -> Check:
    """Definitions v5.0: a department is classified as an A&E type only if it averages over 200 attendances a month.
    The check uses the 12-month average of unbooked plus booked attendances. Series below the threshold are reported and not excluded."""
    series = 0
    low = 0
    for key in TYPE_KEY.values():
        total = (org_month[f"{key}_attendances"] + org_month[f"{key}_booked_attendances"]).groupby(org_month["org_code"]).sum()
        active = total[total > 0]
        series += len(active)
        low += int((active / EXPECTED_MONTHS <= 200).sum())
    return Check("Org-type series averaging 200 or fewer attendances a month (below the definitions' classification threshold; kept as published)",
                 True, "warning", f"{low} of {series} active series")


def run_all(org_month: pd.DataFrame, totals: pd.DataFrame) -> list[Check]:
    return [
        check_months(org_month),
        check_unique_keys(org_month),
        check_no_nulls_or_negatives(org_month),
        check_one_total_per_month(totals),
        check_reconciles_to_published_totals(org_month, totals),
        check_over4_not_above_attendances(org_month),
        check_type1_admissions_within_attendances(org_month),
        check_region_stable(org_month),
        check_type1_orgs_complete(org_month),
        warn_renamed_orgs(org_month),
        warn_dta_12h_above_4_12h(org_month),
        check_type1_providers_use_trust_codes(org_month),
        warn_series_averaging_200_or_less(org_month),
    ]


def failed_errors(checks: list[Check]) -> list[Check]:
    return [c for c in checks if c.severity == "error" and not c.passed]
