"""Run the whole pipeline:  raw CSV -> clean -> validate -> SQLite.

    python scripts/build_database.py

Stops with a non-zero exit code if any error-level validation check fails.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nhs_ed.config import DB_PATH  # noqa: E402
from nhs_ed.pipeline import build  # noqa: E402


def print_check(c) -> None:
    print(f"[{'PASS' if c.passed else 'FAIL'}] ({c.severity}) {c.name} - {c.detail}")


def main() -> int:
    result = build(on_check=print_check)
    if result.errors:
        print(f"\nBuild stopped: {len(result.errors)} error-level check(s) failed.")
        return 1

    print(f"\nRaw rows read: {result.raw_rows:,} | organisation-month rows: {result.org_rows:,} | database: {result.db_path.relative_to(DB_PATH.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
