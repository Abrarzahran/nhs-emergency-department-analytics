"""The raw files have the structure the pipeline relies on."""
import pandas as pd
import pytest

from nhs_ed.config import CLEAN_NUMERIC_COLUMNS, EXPECTED_RAW_COLUMNS, RAW_DIR
from nhs_ed.ingest import SchemaError, check_columns, find_raw_files


def test_twelve_raw_files():
    assert len(find_raw_files(RAW_DIR)) == 12


def test_all_files_share_the_same_22_columns():
    """Headers are identical across files, and contain exactly the columns that are mapped, matched by name and not position."""
    assert len(EXPECTED_RAW_COLUMNS) == 22
    headers = {tuple(pd.read_csv(path, nrows=0).columns) for path in find_raw_files(RAW_DIR)}
    assert len(headers) == 1
    assert set(next(iter(headers))) == set(EXPECTED_RAW_COLUMNS)


def test_clean_column_names_are_unique():
    # Regression test: "Other emergency admissions" once clashed with the Other-A&E-department admissions column.
    assert len(set(CLEAN_NUMERIC_COLUMNS)) == len(CLEAN_NUMERIC_COLUMNS) == 18


def test_cleaned_table_has_no_duplicate_columns(clean):
    assert clean.org_month.columns.is_unique and clean.org_month.shape[1] == 5 + 18


def test_schema_check_rejects_missing_and_extra_columns():
    cols = EXPECTED_RAW_COLUMNS[:-1] + ["Surprise"]
    with pytest.raises(SchemaError) as err:
        check_columns(cols, "demo.csv")
    assert "Other emergency admissions" in str(err.value) and "Surprise" in str(err.value)
