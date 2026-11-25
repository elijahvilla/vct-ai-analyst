"""Checks on the real data/vct.duckdb built from the owner's SQL. Skipped until it exists."""
import os

import duckdb
import pytest

DB = "data/vct.duckdb"
pytestmark = pytest.mark.skipif(not os.path.exists(DB), reason="data/vct.duckdb not built yet")

TABLES = ["dim_event", "dim_team", "dim_player", "dim_agent", "dim_map",
          "fact_map_result", "fact_player_map", "fact_team_comp"]


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect(DB, read_only=True)
    yield c
    c.close()


def test_all_tables_exist(con):
    have = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()}
    assert set(TABLES) <= have


def test_facts_not_empty(con):
    for t in ["fact_player_map", "fact_map_result", "fact_team_comp"]:
        assert con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] > 0, t


def test_agent_roles_valid(con):
    bad = con.execute("SELECT agent_name, role FROM dim_agent WHERE role IS NULL OR role NOT IN ('duelist','initiator','controller','sentinel')").fetchall()
    assert bad == []


def test_dim_keys_unique(con):
    for table, key in [("dim_event", "event_id"), ("dim_team", "team_id"), ("dim_player", "player_id"),
                       ("dim_agent", "agent_name"), ("dim_map", "map_name")]:
        dupes = con.execute(f"SELECT {key} FROM {table} GROUP BY {key} HAVING count(*) > 1").fetchall()
        assert dupes == [], f"{table}.{key} duplicates: {dupes[:5]}"


def test_facts_join_dims(con):
    orphans = con.execute("""
        SELECT count(*) FROM fact_player_map f
        LEFT JOIN dim_agent a ON f.agent_name = a.agent_name
        LEFT JOIN dim_player p ON f.player_id = p.player_id
        WHERE a.agent_name IS NULL OR p.player_id IS NULL""").fetchone()[0]
    assert orphans == 0


def test_kast_range(con):
    lo, hi = con.execute("SELECT min(kast_pct), max(kast_pct) FROM fact_player_map").fetchone()
    assert (0 <= lo and hi <= 1) or (0 <= lo and hi <= 100)


def test_no_side_or_rollup_double_counting(con):
    # each player appears once per map (trap 1: Side rows; trap 2: 'All Maps' rollups)
    dupes = con.execute("SELECT match_map_id, player_id FROM fact_player_map GROUP BY 1, 2 HAVING count(*) > 1 LIMIT 5").fetchall()
    assert dupes == []
    assert con.execute("SELECT count(*) FROM fact_player_map WHERE map_name ILIKE 'all maps'").fetchone()[0] == 0
