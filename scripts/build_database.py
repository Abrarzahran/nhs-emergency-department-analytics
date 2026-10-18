"""Run the whole pipeline:  raw CSV -> clean -> validate -> SQLite.

    python scripts/build_database.py

Stops with a non-zero exit code if any error-level validation check fails.
"""
import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nhs_ed import validate  # noqa: E402
from nhs_ed.clean import clean_raw  # noqa: E402
from nhs_ed.config import DB_PATH, PROCESSED_DIR, RAW_DIR, SOURCE_URL  # noqa: E402
from nhs_ed.db import build_database  # noqa: E402
from nhs_ed.ingest import find_raw_files, load_raw  # noqa: E402


def write_manifest(clean) -> Path:
    """Record the file name, size, SHA-256 and month of each file analysed, so that results are reproducible."""
    month_of = clean.org_month.groupby("source_file")["month_start"].first()
    path = RAW_DIR.parent / "MANIFEST.csv"  # outside data/raw so it is never mistaken for a data file
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "month", "bytes", "sha256", "source_page"])
        for f in sorted(find_raw_files(RAW_DIR), key=lambda p: month_of[p.name]):
            w.writerow([f.name, month_of[f.name].strftime("%Y-%m"), f.stat().st_size,
                        hashlib.sha256(f.read_bytes()).hexdigest(), SOURCE_URL])
    return path


def main() -> int:
    raw = load_raw()
    clean = clean_raw(raw)
    checks = validate.run_all(*clean)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_DIR / "validation_report.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "passed", "severity", "detail"])
        for c in checks:
            w.writerow([c.name, c.passed, c.severity, c.detail])
            print(f"[{'PASS' if c.passed else 'FAIL'}] ({c.severity}) {c.name} - {c.detail}")

    errors = validate.failed_errors(checks)
    if errors:
        print(f"\nBuild stopped: {len(errors)} error-level check(s) failed.")
        return 1

    write_manifest(clean)
    db = build_database(clean)
    print(f"\nRaw rows read: {len(raw):,} | organisation-month rows: {len(clean.org_month):,} | database: {db.relative_to(DB_PATH.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
