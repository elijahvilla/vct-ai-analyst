"""Run one SQL query against data/vct.duckdb and print the result (for exploring while writing the ETL).

Usage: python -m etl.explore "SELECT year, count(*) FROM raw_overview GROUP BY 1"
       python -m etl.explore path/to/query.sql
"""
import os
import sys

import duckdb


def run(sql: str, db_path: str = "data/vct.duckdb", max_rows: int = 50) -> None:
    if os.path.isfile(sql):
        sql = open(sql, encoding="utf-8").read()
    con = duckdb.connect(db_path, read_only=True)
    df = con.execute(sql).fetchdf()
    print(df.head(max_rows).to_string(max_colwidth=40))
    print(f"({len(df):,} rows)")


if __name__ == "__main__":
    run(sys.argv[1])
