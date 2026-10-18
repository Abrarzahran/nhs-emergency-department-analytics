"""The build pipeline: raw CSV -> clean -> validate -> SQLite.

Used by `scripts/build_database.py` and by the Streamlit app, which calls it
when the database file does not exist, for example on Streamlit Community Cloud.
"""
import csv
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import config, validate
from .clean import clean_raw
from .db import build_database
from .ingest import find_raw_files, load_raw


@dataclass
class BuildResult:
    checks: list = field(default_factory=list)
    raw_rows: int = 0
    org_rows: int = 0
    db_path: Path | None = None  # None when an error-level check failed and no database was written

    @property
    def errors(self) -> list:
        return validate.failed_errors(self.checks)


def write_manifest(clean) -> Path:
    """Record the file name, size, SHA-256 and month of each file analysed, so that results are reproducible."""
    month_of = clean.org_month.groupby("source_file")["month_start"].first()
    path = config.RAW_DIR.parent / "MANIFEST.csv"  # outside data/raw so it is never mistaken for a data file
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "month", "bytes", "sha256", "source_page"])
        for f in sorted(find_raw_files(config.RAW_DIR), key=lambda p: month_of[p.name]):
            w.writerow([f.name, month_of[f.name].strftime("%Y-%m"), f.stat().st_size,
                        hashlib.sha256(f.read_bytes()).hexdigest(), config.SOURCE_URL])
    return path


def write_validation_report(checks) -> Path:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = config.PROCESSED_DIR / "validation_report.csv"
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "passed", "severity", "detail"])
        for c in checks:
            w.writerow([c.name, c.passed, c.severity, c.detail])
    return path


def build(db_path: Path | None = None, write_reports: bool = True,
          on_check: Callable | None = None) -> BuildResult:
    """Run the whole pipeline. The database is written to a temporary file and moved into place,
    so a reader never sees a half-built file.

    write_reports=False skips rewriting data/MANIFEST.csv and data/processed/validation_report.csv,
    which are committed to the repository.
    """
    db_path = Path(db_path or config.DB_PATH)
    raw = load_raw()
    clean = clean_raw(raw)
    checks = validate.run_all(*clean)
    result = BuildResult(checks=checks, raw_rows=len(raw), org_rows=len(clean.org_month))

    if write_reports:
        write_validation_report(checks)
    if on_check:
        for c in checks:
            on_check(c)
    if result.errors:
        return result

    if write_reports:
        write_manifest(clean)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(db_path.name + ".tmp")
    tmp.unlink(missing_ok=True)
    build_database(clean, tmp)
    os.replace(tmp, db_path)
    result.db_path = db_path
    return result
