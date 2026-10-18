"""Run every SQL file in sql/queries/ against the database and print the first rows.

    python scripts/run_queries.py            # print results
    python scripts/run_queries.py --save     # also write each result to data/processed/query_results/*.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from nhs_ed.config import DB_PATH, PROCESSED_DIR, SQL_DIR  # noqa: E402
from nhs_ed.db import connect  # noqa: E402


def main() -> None:
    save = "--save" in sys.argv
    out_dir = PROCESSED_DIR / "query_results"
    if save:
        out_dir.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200, "display.max_columns", 20, "display.max_colwidth", 60)
    con = connect(DB_PATH)
    for path in sorted((SQL_DIR / "queries").glob("*.sql")):
        sql = path.read_text()
        title = next(line[3:].strip() for line in sql.splitlines() if line.startswith("-- Q"))
        df = pd.read_sql_query(sql, con)
        print(f"\n=== {path.name} :: {title}\n{df.head(12).to_string(index=False)}\n({len(df)} rows)")
        if save:
            df.to_csv(out_dir / f"{path.stem}.csv", index=False)


if __name__ == "__main__":
    main()
