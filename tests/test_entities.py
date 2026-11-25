from analyst.db import schema_summary
from analyst.entities import load_entities, normalize


def test_normalize_kayo():
    assert normalize("KAY/O") == normalize("kayo") == "kayo"


def test_normalize_spaces_and_dots():
    assert normalize(" Gen.G ") == "geng"
    assert normalize("Paper Rex") == "paperrex"


def test_load_entities(mini_con):
    ents = load_entities(mini_con)
    assert "jett" in ents.agents
    assert "ascent" in ents.maps
    assert len(ents.teams) == 3
    assert "tenz" in ents.players
    assert "valorantchampions2024" in ents.events


def test_schema_summary(mini_con):
    summary = schema_summary(mini_con)
    assert "fact_player_map" in summary
    assert "agent_name" in summary["fact_player_map"]
