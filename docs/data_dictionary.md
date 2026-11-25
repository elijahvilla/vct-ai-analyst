# Data dictionary — VCT database (DuckDB)

Pro Valorant (VCT) maps from 2021 to 2026. Only the tables below may be queried. Names of agents are lowercase
(`jett`, `kayo` for KAY/O). Percentages are on a 0–100 scale. Every map appears once per player in `fact_player_map`.

## dim_event — tournaments
- `event_id` INTEGER — tournament ID (from vlr.gg)
- `event_name` TEXT — e.g. `Valorant Champions 2024`, `Champions Tour 2024: Masters Madrid`, `VCT 2025: EMEA Stage 1`
- `year` INTEGER — season, 2021–2026
- `is_international` BOOLEAN — true for top-tier events: every event from 2023 on, plus Masters and Valorant Champions before 2023

## dim_team — teams
- `team_id` INTEGER — surrogate key
- `team_name` TEXT — full name, e.g. `Sentinels`, `FNATIC`, `Paper Rex`

## dim_player — players
- `player_id` INTEGER — surrogate key (players are identified by in-game name)
- `player_name` TEXT — e.g. `TenZ`, `aspas`

## dim_agent — agents
- `agent_name` TEXT — lowercase, e.g. `jett`, `sova`, `kayo`
- `role` TEXT — `duelist`, `initiator`, `controller` or `sentinel`

## dim_map — maps
- `map_name` TEXT — e.g. `Ascent`, `Bind`, `Haven`, `Lotus`, `Sunset`

## fact_map_result — one row per map played
- `match_map_id` INTEGER — key of the map
- `event_id` INTEGER — join to dim_event
- `year` INTEGER — season
- `stage` TEXT — e.g. `Group Stage`, `Playoffs`
- `match_type` TEXT — e.g. `Upper Final`, `Grand Final`
- `match_name` TEXT — e.g. `Gen.G vs Sentinels`
- `map_name` TEXT — join to dim_map
- `team_a_id`, `team_b_id` INTEGER — join to dim_team
- `winner_team_id` INTEGER — winning team (NULL if no winner recorded)
- `team_a_score`, `team_b_score` INTEGER — rounds won
- `went_overtime` BOOLEAN
- `duration` TEXT — e.g. `46:45`

## fact_player_map — one row per player per map
- `match_map_id` INTEGER — join to fact_map_result
- `player_id` INTEGER — join to dim_player
- `team_id` INTEGER — the player's team, join to dim_team
- `agent_name` TEXT — agent played, join to dim_agent
- `rating` DOUBLE — vlr.gg rating
- `acs` INTEGER — average combat score
- `kills`, `deaths`, `assists` INTEGER
- `kast_pct` DOUBLE — KAST %, 0–100
- `adr` INTEGER — average damage per round
- `headshot_pct` DOUBLE — headshot %, 0–100
- `first_kills`, `first_deaths` INTEGER

## fact_team_comp — one row per agent a team played on a map
- `game_id` INTEGER — same as match_map_id
- `event_id` INTEGER, `year` INTEGER, `map_name` TEXT
- `team_id`, `opponent_id` INTEGER — join to dim_team
- `result` TEXT — `win`, `loss` or `draw`
- `agent_name` TEXT — join to dim_agent

## How to compute common stats
- **Agent pick rate on a map** = maps where a team played the agent ÷ (2 × maps played on that map), from `fact_team_comp`.
- **Agent win rate** = rows with `result = 'win'` ÷ all rows for that agent, from `fact_team_comp`.
- **Map count** = `count(DISTINCT match_map_id)` — never count player rows as maps.
