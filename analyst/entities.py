"""Known names (agents, maps, teams, players, events) used by the grounding check."""
import re
from dataclasses import dataclass, field

import duckdb


def normalize(name: str) -> str:
    """Lowercase and drop spaces and punctuation so 'KAY/O', 'kayo' and 'Kay-O' match."""
    return re.sub(r"[\s/\-.'’:]", "", str(name).strip().lower())


@dataclass
class Entities:
    agents: set[str] = field(default_factory=set)
    maps: set[str] = field(default_factory=set)
    teams: set[str] = field(default_factory=set)
    players: set[str] = field(default_factory=set)
    events: set[str] = field(default_factory=set)


def _names(con: duckdb.DuckDBPyConnection, sql: str) -> set[str]:
    return {normalize(r[0]) for r in con.execute(sql).fetchall() if r[0] is not None}


def load_entities(con: duckdb.DuckDBPyConnection) -> Entities:
    return Entities(
        agents=_names(con, "SELECT agent_name FROM dim_agent"),
        maps=_names(con, "SELECT map_name FROM dim_map"),
        teams=_names(con, "SELECT team_name FROM dim_team"),
        players=_names(con, "SELECT player_name FROM dim_player"),
        events=_names(con, "SELECT event_name FROM dim_event"),
    )
