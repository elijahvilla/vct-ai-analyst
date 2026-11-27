# Data dictionary — VCT database (DuckDB)

Pro Valorant (VCT) maps from 2021 to 2026. Only the tables below may be queried. Names of agents are lowercase
(`jett`, `kayo` for KAY/O). Percentages are on a 0–100 scale. Every map appears once per player in `fact_player_map`.

## What's in the data (use these exact names)

- **Seasons:** 2021–2026. Every Valorant Champions from 2021 to 2025 is included; 2026 runs through Masters Santiago and Masters London plus each league's Kickoff and Stage 1.
- **Agents (lowercase):** astra (controller), brimstone (controller), clove (controller), harbor (controller), miks (controller), omen (controller), viper (controller), iso (duelist), jett (duelist), neon (duelist), phoenix (duelist), raze (duelist), reyna (duelist), waylay (duelist), yoru (duelist), breach (initiator), fade (initiator), gekko (initiator), kayo (initiator), skye (initiator), sova (initiator), tejo (initiator), chamber (sentinel), cypher (sentinel), deadlock (sentinel), killjoy (sentinel), sage (sentinel), veto (sentinel), vyse (sentinel).
- **Maps:** Abyss, Ascent, Bind, Breeze, Corrode, Fracture, Haven, Icebox, Lotus, Pearl, Split, Summit, Sunset.
- **Event names** follow vlr.gg. People often shorten them ("Masters Madrid 2024" = `Champions Tour 2024: Masters Madrid`), so match events by keywords, e.g.
  `event_name ILIKE '%masters%' AND event_name ILIKE '%madrid%' AND year = 2024` — never ILIKE the user's whole phrase.
- **International (top-tier) events by year:**
- **2021:** `Valorant Champions 2021`; `Valorant Champions Tour Stage 2: Masters Reykjavík`; `Valorant Champions Tour Stage 3: Masters Berlin`
- **2022:** `Valorant Champions 2022`; `Valorant Champions Tour Stage 1: Masters Reykjavík`; `Valorant Champions Tour Stage 2: Masters Copenhagen`
- **2023:** `Champions Tour 2023: Americas Last Chance Qualifier`; `Champions Tour 2023: Americas League`; `Champions Tour 2023: Champions China Qualifier`; `Champions Tour 2023: EMEA Last Chance Qualifier`; `Champions Tour 2023: EMEA League`; `Champions Tour 2023: Lock-In Sao Paulo`; `Champions Tour 2023: Masters Tokyo`; `Champions Tour 2023: Pacific Last Chance Qualifier`; `Champions Tour 2023: Pacific League`; `Valorant Champions 2023`
- **2024:** `Champions Tour 2024: Americas Kickoff`; `Champions Tour 2024: Americas Stage 1`; `Champions Tour 2024: Americas Stage 2`; `Champions Tour 2024: China Kickoff`; `Champions Tour 2024: China Stage 1`; `Champions Tour 2024: China Stage 2`; `Champions Tour 2024: EMEA Kickoff`; `Champions Tour 2024: EMEA Stage 1`; `Champions Tour 2024: EMEA Stage 2`; `Champions Tour 2024: Masters Madrid`; `Champions Tour 2024: Masters Shanghai`; `Champions Tour 2024: Pacific Kickoff`; `Champions Tour 2024: Pacific Stage 1`; `Champions Tour 2024: Pacific Stage 2`; `Valorant Champions 2024`
- **2025:** `VCT 2025: Americas Kickoff`; `VCT 2025: Americas Stage 1`; `VCT 2025: Americas Stage 2`; `VCT 2025: China Kickoff`; `VCT 2025: China Stage 1`; `VCT 2025: China Stage 2`; `VCT 2025: EMEA Kickoff`; `VCT 2025: EMEA Stage 1`; `VCT 2025: EMEA Stage 2`; `VCT 2025: Pacific Kickoff`; `VCT 2025: Pacific Stage 1`; `VCT 2025: Pacific Stage 2`; `Valorant Champions 2025`; `Valorant Masters Bangkok 2025`; `Valorant Masters Toronto 2025`
- **2026:** `VCT 2026: Americas Kickoff`; `VCT 2026: Americas Stage 1`; `VCT 2026: China Kickoff`; `VCT 2026: China Stage 1`; `VCT 2026: EMEA Kickoff`; `VCT 2026: EMEA Stage 1`; `VCT 2026: Pacific Kickoff`; `VCT 2026: Pacific Stage 1`; `Valorant Masters London 2026`; `Valorant Masters Santiago 2026`

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
