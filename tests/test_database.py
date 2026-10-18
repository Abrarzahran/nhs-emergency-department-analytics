"""SQLite layer: structure, constraints, and agreement with the cleaned data."""
import sqlite3

import pandas as pd
import pytest

from nhs_ed import queries
from nhs_ed.config import SQL_DIR


@pytest.fixture()
def con(db_path):
    c = sqlite3.connect(db_path)
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()


def count(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_row_counts_match_cleaned_data(con, clean):
    org_month, _ = clean
    assert count(con, "dim_month") == 12
    assert count(con, "dim_org") == org_month.org_code.nunique() == 205
    assert count(con, "fact_org_month") == len(org_month)
    assert count(con, "fact_ae_type_month") == 3 * len(org_month)
    assert count(con, "published_totals") == 12


def test_no_foreign_key_violations(con):
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


def test_attendances_in_db_equal_raw_column_sums(con, clean):
    om = clean.org_month
    expected = {"Type 1": om.t1_attendances.sum(), "Type 2": om.t2_attendances.sum(), "Other": om.oth_attendances.sum()}
    got = dict(con.execute("SELECT ae_type, SUM(attendances) FROM fact_ae_type_month GROUP BY ae_type"))
    assert got == expected


def test_database_sums_match_published_totals_by_month(con):
    matched = con.execute("""
        SELECT COUNT(*) FROM (
          SELECT month_start, SUM(attendances) s FROM fact_ae_type_month WHERE ae_type = 'Type 1' GROUP BY month_start) a
        JOIN published_totals p ON p.month_start = a.month_start AND p.t1_attendances = a.s""").fetchone()[0]
    assert matched == 12


def test_database_refuses_waits_over_4h_above_attendances(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO fact_ae_type_month VALUES ('RAL','2025-04-01','Type 2',10,0,11,0,0)")


def test_database_refuses_unknown_organisation(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO fact_org_month VALUES ('NOPE','2025-04-01',0,0,0)")


def test_database_refuses_unknown_ae_type(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO fact_ae_type_month VALUES ('RAL','2025-04-01','Type 9',1,0,0,0,0)")


def test_every_analysis_query_runs_and_returns_rows(con):
    files = sorted((SQL_DIR / "queries").glob("*.sql"))
    assert len(files) >= 9
    for f in files:
        assert len(pd.read_sql_query(f.read_text(), con)) > 0, f.name


# Guarantees that A&E types are not mixed
def test_trust_ranking_contains_only_organisations_with_type1_activity(con, clean):
    ranked = pd.read_sql_query((SQL_DIR / "queries" / "03_trust_ranking_type1.sql").read_text(), con)
    t1_orgs = set(clean.org_month.query("t1_attendances > 0").org_code)
    assert set(ranked.org_code) <= t1_orgs
    assert "RP6" not in set(ranked.org_code)  # Moorfields: Type 2 only
    assert len(ranked) == 118  # 121 Type 1 organisations minus 3 children's/women's (Liverpool Women's has no Type 1 activity)
    assert not (set(ranked.org_code) & {"RBS", "RCU", "RQ3"})  # children's / women's providers excluded


def test_trust_league_table_total_equals_published_type1_total(db_path, clean):
    c = sqlite3.connect(db_path)
    df = queries.trust_summary(c, "Type 1", queries.regions(c), "2025-04-01", "2026-03-01", exclude_children_womens=False)
    assert df.attendances.sum() == clean.totals.t1_attendances.sum()
    assert len(df) == 121


def test_region_filter_changes_results(db_path):
    c = sqlite3.connect(db_path)
    london = queries.monthly_by_type(c, ["London"], "2025-04-01", "2026-03-01")
    everywhere = queries.monthly_by_type(c, queries.regions(c), "2025-04-01", "2026-03-01")
    assert london.attendances.sum() < everywhere.attendances.sum()
