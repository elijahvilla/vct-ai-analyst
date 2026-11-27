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
    rollups = con.execute("SELECT count(*) FROM fact_player_map JOIN fact_map_result USING (match_map_id) WHERE map_name ILIKE 'all maps'").fetchone()[0]
    assert rollups == 0


# ---------- ready-made metrics (etl/sql/03_metrics.sql), checked against the gold answers in eval/questions.yaml

def _agg_pick_rate(con, event, agent):
    return con.execute("""
        SELECT round(100.0 * sum(team_maps) / (2 * sum(maps_played)), 1) FROM metric_agent_event_map m
        JOIN dim_event e USING (event_id) WHERE e.event_name = ? AND agent_name = ?""", [event, agent]).fetchone()[0]


def test_metric_pick_rate_matches_gold(con):
    # gold a1: Omen 62.2% at Valorant Champions 2024
    assert _agg_pick_rate(con, "Valorant Champions 2024", "omen") == 62.2


def test_metric_maps_with_agent_counts_each_map_once(con):
    # gold t3: Jett was picked on 528 maps in 2024 (both teams picking her counts once)
    assert con.execute("SELECT sum(maps_with_agent) FROM metric_agent_event_map WHERE year = 2024 AND agent_name = 'jett'").fetchone()[0] == 528


def test_metric_team_wins_match_gold(con):
    # gold f4: Sentinels won 48 maps in 2024
    assert con.execute("""SELECT sum(maps_won) FROM metric_team_event_map m JOIN dim_team t USING (team_id)
                          WHERE m.year = 2024 AND t.team_name = 'Sentinels'""").fetchone()[0] == 48


def test_metric_player_kills_match_gold(con):
    # gold f7: aspas had 1312 kills in 2025
    assert con.execute("""SELECT sum(kills) FROM metric_player_event m JOIN dim_player p USING (player_id)
                          WHERE m.year = 2025 AND p.player_name = 'aspas'""").fetchone()[0] == 1312


def test_no_raw_views_left_in_published_db(con):
    views = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_type = 'VIEW'").fetchone()[0]
    assert views == 0


def test_metric_year_pick_rate_matches_raw_facts(con):
    # Chamber was not played at every 2024 event; the yearly pick rate must still use all 2024 maps
    from_metric = con.execute("""SELECT round(100.0 * sum(team_maps) / (2 * sum(maps_played)), 1)
                                 FROM metric_agent_event_map WHERE year = 2024 AND agent_name = 'chamber'""").fetchone()[0]
    from_facts = con.execute("""SELECT round(100.0 * (SELECT count(DISTINCT (game_id, team_id)) FROM fact_team_comp
                                 WHERE year = 2024 AND agent_name = 'chamber') / (2 * count(*)), 1)
                                 FROM fact_map_result WHERE year = 2024""").fetchone()[0]
    assert from_metric == from_facts
