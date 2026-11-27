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

## Ready-made metrics (PREFER these for pick rates, win rates and season totals)

### metric_agent_event_map — one row per event + map + agent
- `event_id`, `year`, `map_name`, `agent_name`, `role`
- `team_maps` INTEGER — times a team played the agent on that map (if both teams picked it, it counts 2)
- `team_maps_won` INTEGER — of those, how many the team won
- `maps_with_agent` INTEGER — maps where at least one team played the agent (both teams picking it counts 1)
- `maps_played` INTEGER — maps played on that map at that event
- `pick_rate_pct`, `win_rate_pct` DOUBLE — for this single row only

### metric_team_event_map — one row per event + map + team
- `event_id`, `year`, `map_name`, `team_id`, `maps_played`, `maps_won`, `win_rate_pct`

### metric_player_event — one row per event + player + team
- `event_id`, `year`, `player_id`, `team_id`, `maps_played`, `kills`, `deaths`, `assists`, `first_kills`,
  `avg_rating`, `avg_acs` (averages over that event's maps)

## How to compute common stats
- **Combining rows: never average the `_pct` columns.** Sum the counts, then divide:
  - agent pick rate = `100 * sum(team_maps) / (2 * sum(maps_played))`
  - agent win rate  = `100 * sum(team_maps_won) / sum(team_maps)`
  - team win rate   = `100 * sum(maps_won) / sum(maps_played)`
  - player average rating over several events = weight by maps: `sum(avg_rating * maps_played) / sum(maps_played)`
- **"How many maps was X picked on"** = `sum(maps_with_agent)`; "how many times was X picked" = `sum(team_maps)`.
- **Map count** = `count(DISTINCT match_map_id)` in fact tables — never count player rows as maps.
- Filter events with `dim_event` (name, year, is_international) and join on `event_id`.
