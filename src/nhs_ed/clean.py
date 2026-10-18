"""Turn the raw text rows into tidy, typed tables.

Output
------
org_month : one row per organisation per month (wide, 18 numeric columns)
totals    : the 12 "TOTAL" rows NHS England publishes, kept only so that
            validate.py can prove our rows add up to the published totals
"""
import calendar
import re
from typing import NamedTuple

import pandas as pd

from .config import (
    AE_TYPES,
    CLEAN_NUMERIC_COLUMNS,
    MEASURES,
    ORG_LEVEL_COLUMNS,
    RAW_NUMERIC_COLUMNS,
    RAW_TO_CLEAN,
    REGION_MAP,
    SPECIALIST_NAME_PATTERN,
    TYPE_KEY,
)

_MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_name) if m}
_PERIOD_RE = re.compile(r"^MSitAE-([A-Z]+)-(\d{4})$", re.IGNORECASE)


class CleanData(NamedTuple):
    org_month: pd.DataFrame
    totals: pd.DataFrame


def parse_period(period: str) -> pd.Timestamp:
    """'MSitAE-JUNE-2025' -> Timestamp('2025-06-01')."""
    match = _PERIOD_RE.match(period.strip())
    if not match or match.group(1).upper() not in _MONTHS:
        raise ValueError(f"Unrecognised Period value: {period!r}")
    return pd.Timestamp(year=int(match.group(2)), month=_MONTHS[match.group(1).upper()], day=1)


def display_name(name: str) -> str:
    """'KING'S COLLEGE HOSPITAL NHS FOUNDATION TRUST' -> "King's College Hospital NHS Foundation Trust"."""
    out = name.title()
    out = re.sub(r"'S\b", "'s", out)
    for acronym in ("NHS", "UTC", "UCC", "MIU", "WIC", "OOH", "CIC", "CBS", "NEMS", "QMS", "GP", "LLR", "EA", "UK"):
        out = re.sub(rf"\b{acronym.title()}\b", acronym, out)
    for small in ("And", "Of", "The"):
        out = re.sub(rf"(?<=\w) {small} ", f" {small.lower()} ", out)
    return out


def clean_raw(raw: pd.DataFrame) -> CleanData:
    df = raw.copy()

    # Whitespace: 'Parent Org' has trailing spaces in most rows ("NHS ENGLAND SOUTH EAST ").
    for col in ["Period", "Org Code", "Parent Org", "Org name"]:
        df[col] = df[col].str.strip()

    # Separate the published TOTAL row from organisation rows.
    #    The key is Org Code and not Period, because in the February 2026 file the TOTAL row
    #    carries the real period ("MSitAE-FEBRUARY-2026") instead of "TOTAL".
    is_total = df["Org Code"].str.upper().eq("TOTAL")
    orgs, totals = df[~is_total].copy(), df[is_total].copy()

    # Month: parsed from Period on organisation rows; each file must hold one month.
    orgs["month_start"] = orgs["Period"].map(parse_period)
    months_per_file = orgs.groupby("source_file")["month_start"].nunique()
    if (months_per_file != 1).any():
        raise ValueError(f"Files with more than one Period: {months_per_file[months_per_file != 1].to_dict()}")
    month_of_file = orgs.groupby("source_file")["month_start"].first()
    totals["month_start"] = totals["source_file"].map(month_of_file)

    # Numbers: explicit conversion; errors="raise" so bad values cannot slip through.
    for table in (orgs, totals):
        for col in RAW_NUMERIC_COLUMNS:
            table[col] = pd.to_numeric(table[col], errors="raise").astype("int64")

    # Clean column names and region labels.
    orgs = orgs.rename(columns=RAW_TO_CLEAN).rename(columns={"Org Code": "org_code", "Org name": "org_name"})
    totals = totals.rename(columns=RAW_TO_CLEAN)

    unknown = set(orgs["Parent Org"]) - set(REGION_MAP)
    if unknown:
        raise ValueError(f"Unknown Parent Org values: {unknown}")
    orgs["region"] = orgs["Parent Org"].map(REGION_MAP)

    keep = ["org_code", "org_name", "region", "month_start", "source_file"] + CLEAN_NUMERIC_COLUMNS
    org_month = orgs[keep].sort_values(["month_start", "org_code"]).reset_index(drop=True)
    totals = totals[["month_start", "source_file"] + CLEAN_NUMERIC_COLUMNS].sort_values("month_start").reset_index(drop=True)
    return CleanData(org_month, totals)


# Derived tables
def build_dim_org(org_month: pd.DataFrame) -> pd.DataFrame:
    """One row per organisation. Name = the name used in its most recent month,
    because four organisations were renamed during the year (e.g. RA2)."""
    latest = org_month.sort_values("month_start").groupby("org_code").tail(1).set_index("org_code")
    has_type1 = org_month.groupby("org_code")["t1_attendances"].max().gt(0)
    dim = pd.DataFrame(
        {
            "org_name": latest["org_name"],
            "org_name_display": latest["org_name"].map(display_name),
            "region": latest["region"],
            "has_type1": has_type1.astype(int),
        }
    )
    dim["is_children_or_womens"] = dim["org_name"].str.contains(SPECIALIST_NAME_PATTERN, regex=True).astype(int)
    return dim.reset_index().sort_values("org_code").reset_index(drop=True)


def build_dim_month(org_month: pd.DataFrame) -> pd.DataFrame:
    months = org_month[["month_start", "source_file"]].drop_duplicates().sort_values("month_start")
    months["month_label"] = months["month_start"].dt.strftime("%b %Y")
    months["days_in_month"] = months["month_start"].map(lambda d: calendar.monthrange(d.year, d.month)[1])
    return months.reset_index(drop=True)


def to_long_by_type(org_month: pd.DataFrame) -> pd.DataFrame:
    """Convert the wide columns, such as t1_attendances and t2_attendances, to long format with one row per organisation, month and A&E type.

    Long format is what makes 'never mix A&E types' easy to enforce in SQL:
    every query has to say which ae_type it is looking at.
    """
    parts = []
    for ae_type in AE_TYPES:
        key = TYPE_KEY[ae_type]
        part = org_month[["org_code", "month_start"]].copy()
        part["ae_type"] = ae_type
        for measure in MEASURES:
            part[measure] = org_month[f"{key}_{measure}"]
        parts.append(part)
    return pd.concat(parts, ignore_index=True).sort_values(["month_start", "org_code", "ae_type"]).reset_index(drop=True)


def build_org_level(org_month: pd.DataFrame) -> pd.DataFrame:
    return org_month[["org_code", "month_start", *ORG_LEVEL_COLUMNS]].copy()
