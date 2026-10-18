"""Build the SQLite database from the cleaned tables."""
import sqlite3
from pathlib import Path

import pandas as pd

from .clean import CleanData, build_dim_month, build_dim_org, build_org_level, to_long_by_type
from .config import CLEAN_NUMERIC_COLUMNS, DB_PATH, SQL_DIR


def _iso(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month_start"] = out["month_start"].dt.strftime("%Y-%m-%d")
    return out


def build_database(clean: CleanData, db_path: Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    org_month, totals = clean

    with sqlite3.connect(db_path) as con:
        con.executescript((SQL_DIR / "schema.sql").read_text())  # drops + recreates tables
        con.execute("PRAGMA foreign_keys = ON")

        # Parent tables first because of the foreign keys, then the fact tables
        _iso(build_dim_month(org_month)).to_sql("dim_month", con, if_exists="append", index=False)
        build_dim_org(org_month).to_sql("dim_org", con, if_exists="append", index=False)
        _iso(to_long_by_type(org_month)).to_sql("fact_ae_type_month", con, if_exists="append", index=False)
        _iso(build_org_level(org_month)).to_sql("fact_org_month", con, if_exists="append", index=False)

        pt = _iso(totals[["month_start", *CLEAN_NUMERIC_COLUMNS]])
        pt.to_sql("published_totals", con, if_exists="append", index=False)

        con.executescript((SQL_DIR / "views.sql").read_text())
        violations = con.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign key violations: {violations[:5]}")
    return db_path


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    return con
