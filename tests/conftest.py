import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nhs_ed.clean import clean_raw  # noqa: E402
from nhs_ed.config import EXPECTED_RAW_COLUMNS, RAW_DIR  # noqa: E402
from nhs_ed.db import build_database  # noqa: E402
from nhs_ed.ingest import load_raw  # noqa: E402


@pytest.fixture(scope="session")
def raw():
    return load_raw(RAW_DIR)


@pytest.fixture(scope="session")
def clean(raw):
    return clean_raw(raw)


@pytest.fixture(scope="session")
def db_path(clean, tmp_path_factory):
    """A temporary database built from the real data. It does not touch data/processed."""
    return build_database(clean, tmp_path_factory.mktemp("db") / "test.sqlite")


def make_raw(rows: list[dict], file="synthetic.csv") -> pd.DataFrame:
    """Build a tiny raw-format frame. Unspecified numeric columns default to '0'."""
    out = []
    for r in rows:
        base = {c: "0" for c in EXPECTED_RAW_COLUMNS}
        base.update({"Period": "MSitAE-JUNE-2025", "Parent Org": "NHS ENGLAND LONDON ", "source_file": file})
        base.update(r)
        out.append(base)
    return pd.DataFrame(out)
