"""External check: do our calculations reproduce figures NHS England itself published?

The expected values below were transcribed from NHS England's monthly "A&E Attendances and Emergency Admissions
Statistical Commentary" PDFs (URLs in docs/OFFICIAL_RECONCILIATION.md). They were not used to tune any calculation:
the calculation was fixed first (summed counts, booked appointments included) and these tests record how it compares.

NB: the CSVs supplied are the later *revised* files, so tiny differences from a commentary written at publication
time are possible and are asserted explicitly below rather than hidden.
"""
import pytest

from nhs_ed.metrics import pct_within_4h

# month -> Type 1 % within 4 hours as published
OFFICIAL_TYPE1 = {"2025-04": 60.2, "2025-09": 61.1, "2025-10": 60.1, "2025-11": 60.3,
                  "2025-12": 59.6, "2026-01": 57.3, "2026-02": 59.4, "2026-03": 64.1}
# month -> all-department % within 4 hours as published
OFFICIAL_ALL = {"2025-09": 75.1, "2025-11": 74.2, "2025-12": 73.8, "2026-01": 72.5, "2026-02": 74.1, "2026-03": 77.1}


@pytest.fixture(scope="module")
def monthly(clean):
    om = clean.org_month.copy()
    om["m"] = om.month_start.dt.strftime("%Y-%m")
    return om.groupby("m").sum(numeric_only=True)


def type1_pct(row, include_booked=True):
    return pct_within_4h(row.t1_attendances + (row.t1_booked_attendances if include_booked else 0),
                         row.t1_over_4hrs + (row.t1_booked_over_4hrs if include_booked else 0))


def all_pct(row):
    att = sum(row[f"{k}_attendances"] + row[f"{k}_booked_attendances"] for k in ("t1", "t2", "oth"))
    over = sum(row[f"{k}_over_4hrs"] + row[f"{k}_booked_over_4hrs"] for k in ("t1", "t2", "oth"))
    return pct_within_4h(att, over)


@pytest.mark.parametrize("month,published", OFFICIAL_TYPE1.items())
def test_type1_performance_matches_published_when_booked_included(monthly, month, published):
    assert round(type1_pct(monthly.loc[month]), 1) == published


@pytest.mark.parametrize("month,published", OFFICIAL_ALL.items())
def test_all_department_performance_matches_published(monthly, month, published):
    assert round(all_pct(monthly.loc[month]), 1) == published


def test_documented_difference_october_2025_all_departments(monthly):
    # Published 74.1, and the supplied file gives 74.2. The cause is unconfirmed, as set out in OFFICIAL_RECONCILIATION.md.
    assert abs(all_pct(monthly.loc["2025-10"]) - 74.1) < 0.15  # actual: 74.19 vs 74.1 published


def test_excluding_booked_does_not_reproduce_published_type1(monthly):
    """Guards the decision: the unbooked-only basis misses the published headline in every month."""
    misses = [m for m, p in OFFICIAL_TYPE1.items() if round(type1_pct(monthly.loc[m], include_booked=False), 1) != p]
    assert len(misses) == len(OFFICIAL_TYPE1)


def test_december_type1_admission_share_matches_published(monthly):
    r = monthly.loc["2025-12"]
    assert round(100 * r.t1_emergency_admissions / (r.t1_attendances + r.t1_booked_attendances), 1) == 27.7


def test_january_decision_to_admit_delays_match_published(monthly):
    r = monthly.loc["2026-01"]
    assert r.dta_12h_plus == 71_517                      # "delayed more than 12 hours from decision to admit"
    assert r.dta_4_to_12h + r.dta_12h_plus == 161_141    # "over 4 hour delays from decision to admit to admission"


def test_october_booked_attendances_match_published(monthly):
    r = monthly.loc["2025-10"]
    assert r.t1_booked_attendances + r.t2_booked_attendances + r.oth_booked_attendances == 83_524


def test_121_trusts_have_type1_departments(clean):
    # Published commentary: "... of 121 reporting trusts with Type 1 departments"
    assert (clean.org_month.groupby("org_code").t1_attendances.max() > 0).sum() == 121
