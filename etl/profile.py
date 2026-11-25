"""Print a quick profile of every CSV under data/raw/: rows, columns, samples, distinct counts."""
import glob
import os
import re

import duckdb

KEY_COLUMNS = re.compile(r"agent|map|team|player|tournament|event|stage|year", re.I)


def profile_csv(path: str) -> dict:
    con = duckdb.connect()
    rel = con.read_csv(path)
    columns = list(zip(rel.columns, [str(t) for t in rel.types]))
    rows = con.execute("SELECT count(*) FROM rel").fetchone()[0]
    distinct = {
        c: con.execute(f'SELECT count(DISTINCT "{c}") FROM rel').fetchone()[0]
        for c, _ in columns
        if KEY_COLUMNS.search(c)
    }
    sample = con.execute("SELECT * FROM rel LIMIT 3").fetchdf()
    return {"path": path, "rows": rows, "columns": columns, "distinct": distinct, "sample": sample}


def main(raw_dir: str = "data/raw") -> None:
    files = sorted(glob.glob(os.path.join(raw_dir, "**", "*.csv"), recursive=True))
    if not files:
        print(f"No CSVs in {raw_dir}. Run python -m data.download first.")
    for f in files:
        r = profile_csv(f)
        print(f"\n=== {r['path']}  ({r['rows']:,} rows)")
        for c, t in r["columns"]:
            print(f"  {c}: {t}" + (f"  [{r['distinct'][c]:,} distinct]" if c in r["distinct"] else ""))
        print(r["sample"].to_string(max_colwidth=30))


if __name__ == "__main__":
    main()
