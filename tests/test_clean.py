"""Cleaning rules, tested on small synthetic frames where the right answer is obvious."""
import pandas as pd
import pytest
from conftest import make_raw

from nhs_ed.clean import build_dim_org, clean_raw, display_name, parse_period, to_long_by_type


@pytest.mark.parametrize("text,expected", [
    ("MSitAE-JUNE-2025", "2025-06-01"), ("MSitAE-FEBRUARY-2026", "2026-02-01"), (" MSitAE-APRIL-2025 ", "2025-04-01")])
def test_parse_period(text, expected):
    assert parse_period(text) == pd.Timestamp(expected)


@pytest.mark.parametrize("bad", ["TOTAL", "MSitAE-JUNO-2025", "JUNE 2025", ""])
def test_parse_period_rejects_garbage(bad):
    with pytest.raises(ValueError):
        parse_period(bad)


def _two_orgs_and_total(total_period="TOTAL"):
    return make_raw([
        {"Org Code": "AAA", "Org name": "ALPHA NHS TRUST", "A&E attendances Type 1": "100", "Attendances over 4hrs Type 1": "40"},
        {"Org Code": "BBB", "Org name": "BETA NHS TRUST", "A&E attendances Type 1": "50", "Attendances over 4hrs Type 1": "5"},
        {"Org Code": "TOTAL", "Org name": "TOTAL", "Parent Org": "TOTAL", "Period": total_period,
         "A&E attendances Type 1": "150", "Attendances over 4hrs Type 1": "45"},
    ])


@pytest.mark.parametrize("total_period", ["TOTAL", "MSitAE-JUNE-2025"])  # the 2nd form is how the Feb-2026 file does it
def test_total_row_is_removed_whatever_its_period_says(total_period):
    org_month, totals = clean_raw(_two_orgs_and_total(total_period))
    assert list(org_month.org_code) == ["AAA", "BBB"]
    assert len(totals) == 1 and totals.t1_attendances.iloc[0] == 150
    assert totals.month_start.iloc[0] == pd.Timestamp("2025-06-01")  # month taken from the file's other rows


def test_whitespace_stripped_and_region_labelled():
    org_month, _ = clean_raw(_two_orgs_and_total())
    assert set(org_month.region) == {"London"}  # source had "NHS ENGLAND LONDON " with a trailing space


def test_numbers_become_integers():
    org_month, _ = clean_raw(_two_orgs_and_total())
    assert str(org_month.t1_attendances.dtype) == "int64"


def test_non_numeric_value_stops_the_pipeline():
    raw = _two_orgs_and_total()
    raw.loc[0, "A&E attendances Type 1"] = "n/a"
    with pytest.raises(ValueError):
        clean_raw(raw)


def test_unknown_region_stops_the_pipeline():
    raw = _two_orgs_and_total()
    raw.loc[0, "Parent Org"] = "NHS ENGLAND ATLANTIS"
    with pytest.raises(ValueError):
        clean_raw(raw)


def test_dim_org_uses_most_recent_name():
    raw = pd.concat([
        make_raw([{"Org Code": "RA2", "Org name": "OLD NAME NHS TRUST", "Period": "MSitAE-APRIL-2025"}], file="apr.csv"),
        make_raw([{"Org Code": "RA2", "Org name": "NEW NAME NHS TRUST", "Period": "MSitAE-MAY-2025"}], file="may.csv"),
    ], ignore_index=True)
    dim = build_dim_org(clean_raw(raw).org_month)
    assert len(dim) == 1 and dim.org_name.iloc[0] == "NEW NAME NHS TRUST"


def test_long_format_has_one_row_per_type_and_preserves_counts():
    org_month, _ = clean_raw(_two_orgs_and_total())
    long = to_long_by_type(org_month)
    assert len(long) == 2 * 3
    assert long.query("ae_type == 'Type 1'").attendances.sum() == 150
    assert long.query("ae_type != 'Type 1'").attendances.sum() == 0


def test_children_and_womens_flag():
    raw = make_raw([{"Org Code": "X1", "Org name": "ALDER HEY CHILDREN'S NHS FOUNDATION TRUST"},
                    {"Org Code": "X2", "Org name": "LIVERPOOL WOMEN'S NHS FOUNDATION TRUST"},
                    {"Org Code": "X3", "Org name": "ROYAL FREE LONDON NHS FOUNDATION TRUST"}])
    flags = build_dim_org(clean_raw(raw).org_month).set_index("org_code").is_children_or_womens
    assert flags.to_dict() == {"X1": 1, "X2": 1, "X3": 0}


def test_display_name():
    assert display_name("KING'S COLLEGE HOSPITAL NHS FOUNDATION TRUST") == "King's College Hospital NHS Foundation Trust"
    assert display_name("BARKING, HAVERING AND REDBRIDGE UNIVERSITY HOSPITALS NHS TRUST") == "Barking, Havering and Redbridge University Hospitals NHS Trust"
