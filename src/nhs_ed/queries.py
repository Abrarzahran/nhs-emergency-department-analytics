"""Parameterised SQL used by the Streamlit app and reusable in notebooks.

All user choices are passed as bound parameters (?), never pasted into the SQL text,
so a filter value can never change the meaning of a query (SQL-injection safe by design).
The only text we build dynamically is a run of '?' placeholders for IN (...) lists.
"""
import sqlite3
from typing import Sequence

import pandas as pd


def _in(values: Sequence) -> str:
    return "(" + ",".join("?" for _ in values) + ")"


def _frame(con: sqlite3.Connection, sql: str, params: Sequence) -> pd.DataFrame:
    df = pd.read_sql_query(sql, con, params=list(params))
    if "month_start" in df.columns:
        df["month_start"] = pd.to_datetime(df["month_start"])
    return df


def months(con) -> pd.DataFrame:
    return _frame(con, "SELECT month_start, month_label, days_in_month FROM dim_month ORDER BY month_start", [])


def regions(con) -> list[str]:
    return [r[0] for r in con.execute("SELECT DISTINCT region FROM dim_org ORDER BY region")]


def monthly_by_type(con, regs: Sequence[str], start: str, end: str) -> pd.DataFrame:
    """Summed counts per month and A&E type for the chosen regions."""
    sql = f"""
        SELECT v.month_start, v.month_label, v.days_in_month, v.ae_type,
               SUM(v.attendances) AS attendances, SUM(v.over_4hrs) AS over_4hrs,
               SUM(v.booked_attendances) AS booked_attendances, SUM(v.booked_over_4hrs) AS booked_over_4hrs,
               SUM(v.emergency_admissions) AS emergency_admissions
        FROM v_ae_type_month v
        WHERE v.region IN {_in(regs)} AND v.month_start BETWEEN ? AND ?
        GROUP BY v.month_start, v.month_label, v.days_in_month, v.ae_type
        ORDER BY v.month_start, v.ae_type"""
    return _frame(con, sql, [*regs, start, end])


def monthly_by_region(con, ae_type: str, start: str, end: str) -> pd.DataFrame:
    sql = """
        SELECT v.month_start, v.month_label, v.days_in_month, v.region,
               SUM(v.attendances) AS attendances, SUM(v.over_4hrs) AS over_4hrs,
               SUM(v.booked_attendances) AS booked_attendances, SUM(v.booked_over_4hrs) AS booked_over_4hrs,
               SUM(v.emergency_admissions) AS emergency_admissions
        FROM v_ae_type_month v
        WHERE v.ae_type = ? AND v.month_start BETWEEN ? AND ?
        GROUP BY v.month_start, v.month_label, v.days_in_month, v.region
        ORDER BY v.month_start, v.region"""
    return _frame(con, sql, [ae_type, start, end])


def dta_waits_monthly(con, regs: Sequence[str], start: str, end: str) -> pd.DataFrame:
    """Decision-to-admit waits (not split by A&E type in the source) plus all emergency admissions via A&E."""
    sql = f"""
        SELECT f.month_start,
               SUM(f.dta_4_to_12h) AS dta_4_to_12h, SUM(f.dta_12h_plus) AS dta_12h_plus,
               SUM(f.other_emergency_admissions) AS other_emergency_admissions,
               SUM(a.ae_adm) AS ae_emergency_admissions
        FROM fact_org_month f
        JOIN dim_org o ON o.org_code = f.org_code
        JOIN (SELECT org_code, month_start, SUM(emergency_admissions) AS ae_adm
              FROM fact_ae_type_month GROUP BY org_code, month_start) a
             ON a.org_code = f.org_code AND a.month_start = f.month_start
        WHERE o.region IN {_in(regs)} AND f.month_start BETWEEN ? AND ?
        GROUP BY f.month_start ORDER BY f.month_start"""
    return _frame(con, sql, [*regs, start, end])


def trust_summary(con, ae_type: str, regs: Sequence[str], start: str, end: str, exclude_children_womens: bool = True) -> pd.DataFrame:
    """One row per organisation for one A&E type over the chosen months, used for the Type 1 trust ranking."""
    sql = f"""
        SELECT v.org_code, v.org_name, v.region, v.is_children_or_womens,
               SUM(v.attendances) AS attendances, SUM(v.over_4hrs) AS over_4hrs,
               SUM(v.booked_attendances) AS booked_attendances, SUM(v.booked_over_4hrs) AS booked_over_4hrs,
               SUM(v.emergency_admissions) AS emergency_admissions,
               COUNT(DISTINCT CASE WHEN v.attendances > 0 THEN v.month_start END) AS months_reporting
        FROM v_ae_type_month v
        WHERE v.ae_type = ? AND v.region IN {_in(regs)} AND v.month_start BETWEEN ? AND ?
          AND (? = 0 OR v.is_children_or_womens = 0)
        GROUP BY v.org_code, v.org_name, v.region, v.is_children_or_womens
        HAVING SUM(v.attendances) + SUM(v.booked_attendances) > 0"""
    return _frame(con, sql, [ae_type, *regs, start, end, int(exclude_children_womens)])


def trust_dta_summary(con, start: str, end: str) -> pd.DataFrame:
    sql = """
        SELECT f.org_code, SUM(f.dta_4_to_12h) AS dta_4_to_12h, SUM(f.dta_12h_plus) AS dta_12h_plus
        FROM fact_org_month f WHERE f.month_start BETWEEN ? AND ? GROUP BY f.org_code"""
    return _frame(con, sql, [start, end])


def trust_monthly(con, ae_type: str, org_codes: Sequence[str], start: str, end: str) -> pd.DataFrame:
    sql = f"""
        SELECT v.org_code, v.org_name, v.month_start, v.month_label, v.days_in_month,
               v.attendances, v.over_4hrs, v.booked_attendances, v.booked_over_4hrs, v.emergency_admissions
        FROM v_ae_type_month v
        WHERE v.ae_type = ? AND v.org_code IN {_in(org_codes)} AND v.month_start BETWEEN ? AND ?
        ORDER BY v.month_start, v.org_name"""
    return _frame(con, sql, [ae_type, *org_codes, start, end])
