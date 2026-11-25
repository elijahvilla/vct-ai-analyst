"""Tests for etl.build_db.build() itself (the runner), using a tiny fake raw/ folder."""
import duckdb

from etl.build_db import build


def _write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_build_stacks_years_and_runs_sql(tmp_path):
    raw = tmp_path / "raw"
    _write(raw / "vct_2023" / "matches" / "overview.csv", "Player,Kills\nTenZ,20\n")
    _write(raw / "vct_2024" / "matches" / "overview.csv", "Player,Kills\nAspas,25\nDemon1,22\n")
    _write(raw / "all_ids" / "all_teams_ids.csv", "Team,Team ID\nSentinels,2\n")
    sql_dir = tmp_path / "sql"
    _write(sql_dir / "01_x.sql", "CREATE OR REPLACE TABLE kills_by_year AS SELECT year, sum(Kills) AS k FROM raw_overview GROUP BY year;")
    db = tmp_path / "t.duckdb"

    build(raw_dir=str(raw), db_path=str(db), sql_dir=str(sql_dir))

    con = duckdb.connect(str(db), read_only=True)
    assert con.execute("SELECT count(*) FROM raw_overview").fetchone()[0] == 3
    assert con.execute("SELECT count(*) FROM raw_2024_overview").fetchone()[0] == 2
    assert con.execute("SELECT count(*) FROM raw_all_all_teams_ids").fetchone()[0] == 1
    assert dict(con.execute("SELECT year, k FROM kills_by_year").fetchall()) == {2023: 20, 2024: 47}
