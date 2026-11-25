"""Build data/vct.duckdb: register the raw CSVs as views, then run etl/sql/*.sql in order.

Views created:
  raw_<year>_<stem>  one per yearly file, e.g. raw_2024_overview
  raw_<stem>         all years stacked (columns matched by name) plus a `year` column
  raw_all_<stem>     files from data/raw/all_ids/
Usage: python -m etl.build_db
"""
import glob
import os
import re
from collections import defaultdict

import duckdb

# Always honor double-quoted fields (team names contain commas) and sniff the whole file.
CSV_OPTS = "quote='\"', escape='\"', sample_size=-1"


def _q(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def build(raw_dir: str = "data/raw", db_path: str = "data/vct.duckdb", sql_dir: str = "etl/sql") -> None:
    if os.path.exists(db_path):
        os.remove(db_path)
    con = duckdb.connect(db_path)
    by_stem: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(raw_dir, "**", "*.csv"), recursive=True)):
        rel = os.path.relpath(path, raw_dir).replace("\\", "/")
        stem = os.path.splitext(os.path.basename(path))[0]
        m = re.match(r"vct_(\d{4})/", rel)
        if m:
            year = int(m.group(1))
            con.execute(f"CREATE VIEW raw_{year}_{stem} AS SELECT * FROM read_csv_auto('{_q(path)}', {CSV_OPTS})")
            by_stem[stem].append((year, f"raw_{year}_{stem}"))
        elif rel.startswith("all_ids/"):
            con.execute(f"CREATE VIEW raw_all_{stem} AS SELECT * FROM read_csv_auto('{_q(path)}', {CSV_OPTS})")
    for stem, parts in by_stem.items():
        union = " UNION ALL BY NAME ".join(f"SELECT {y} AS year, * FROM {v}" for y, v in parts)
        con.execute(f"CREATE VIEW raw_{stem} AS {union}")
    for sql_file in sorted(glob.glob(os.path.join(sql_dir, "*.sql"))):
        with open(sql_file, encoding="utf-8") as f:
            con.execute(f.read())
    con.close()


if __name__ == "__main__":
    build()
    print("built data/vct.duckdb")
