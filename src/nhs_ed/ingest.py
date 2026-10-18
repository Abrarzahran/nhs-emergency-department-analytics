"""Read the raw monthly CSV files and check their structure."""
from pathlib import Path

import pandas as pd

from .config import EXPECTED_RAW_COLUMNS, RAW_DIR


class SchemaError(ValueError):
    """Raised when a raw file does not have the expected columns."""


def find_raw_files(raw_dir: Path = RAW_DIR) -> list[Path]:
    files = sorted(Path(raw_dir).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    return files


def check_columns(columns, source: str = "file") -> None:
    """Raise an error if the header differs from the expected one."""
    columns = list(columns)
    missing = [c for c in EXPECTED_RAW_COLUMNS if c not in columns]
    extra = [c for c in columns if c not in EXPECTED_RAW_COLUMNS]
    if missing or extra:
        raise SchemaError(f"{source}: missing columns {missing}; unexpected columns {extra}")


def load_raw(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Read every CSV and stack them. Everything is read as text, so that:

    we convert numbers explicitly in clean.py with errors="raise", so a stray
    value like "n/a" or "-" stops the pipeline instead of being silently turned
    into NaN/0.
    """
    frames = []
    for path in find_raw_files(raw_dir):
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        check_columns(df.columns, source=path.name)
        df["source_file"] = path.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
