-- 02_facts.sql — fact tables (one row per event that happened), built after the dims.

-- One row per map played. The natural key is year + tournament + stage + match type +
-- match name + map. A handful of keys repeat (the same map played twice in one series),
-- which makes them impossible to match to player rows, so those are dropped.
CREATE OR REPLACE TABLE fact_map_result AS
WITH keyed AS (
    SELECT *, count(*) OVER (PARTITION BY year, Tournament, Stage, "Match Type", "Match Name", Map) AS key_count
    FROM raw_maps_scores
    WHERE Map IS NOT NULL AND Map <> 'All Maps'
)
SELECT
    row_number() OVER (ORDER BY k.year, k.Tournament, k.Stage, k."Match Type", k."Match Name", k.Map)::INTEGER AS match_map_id,
    e.event_id,
    k.year::INTEGER        AS year,
    k.Stage                AS stage,
    k."Match Type"         AS match_type,
    k."Match Name"         AS match_name,
    k.Map                  AS map_name,
    ta.team_id             AS team_a_id,
    tb.team_id             AS team_b_id,
    CASE WHEN k."Team A Score" > k."Team B Score" THEN ta.team_id
         WHEN k."Team B Score" > k."Team A Score" THEN tb.team_id END AS winner_team_id,
    k."Team A Score"::INTEGER AS team_a_score,
    k."Team B Score"::INTEGER AS team_b_score,
    (coalesce(k."Team A Overtime Score", 0) + coalesce(k."Team B Overtime Score", 0)) > 0 AS went_overtime,
    k.Duration             AS duration
FROM keyed k
JOIN dim_event e ON e.event_name = k.Tournament AND e.year = k.year
JOIN dim_team ta ON ta.team_name = k."Team A"
JOIN dim_team tb ON tb.team_name = k."Team B"
WHERE k.key_count = 1;

-- One row per player per map. Traps handled here:
--   * raw_overview repeats every player-map 3 times (Side = both / attack / defend): keep 'both'.
--   * 'All Maps' rollup rows and rows with no map: dropped.
--   * percentages are text like '81%': converted to numbers 0-100.
--   * a player who switched agents mid-map lists two ('astra, sova'): first agent kept.
CREATE OR REPLACE TABLE fact_player_map AS
SELECT
    m.match_map_id,
    p.player_id,
    t.team_id,
    lower(trim(split_part(o.Agents, ',', 1)))                                    AS agent_name,
    o.Rating::DOUBLE                                                             AS rating,
    o."Average Combat Score"::INTEGER                                            AS acs,
    o.Kills::INTEGER                                                             AS kills,
    o.Deaths::INTEGER                                                            AS deaths,
    o.Assists::INTEGER                                                           AS assists,
    try_cast(replace(o."Kill, Assist, Trade, Survive %", '%', '') AS DOUBLE)     AS kast_pct,
    o."Average Damage Per Round"::INTEGER                                        AS adr,
    try_cast(replace(o."Headshot %", '%', '') AS DOUBLE)                         AS headshot_pct,
    o."First Kills"::INTEGER                                                     AS first_kills,
    o."First Deaths"::INTEGER                                                    AS first_deaths
FROM raw_overview o
JOIN fact_map_result m
  ON m.year = o.year AND m.match_name = o."Match Name" AND m.map_name = o.Map
 AND m.stage = o.Stage AND m.match_type = o."Match Type"
JOIN dim_event e ON e.event_id = m.event_id AND e.event_name = o.Tournament
JOIN dim_player p ON p.player_name = o.Player
JOIN dim_team t ON t.team_name = o.Team AND t.team_id IN (m.team_a_id, m.team_b_id)
WHERE o.Side = 'both'
  AND o.Map IS NOT NULL AND o.Map <> 'All Maps'
  AND o.Agents IS NOT NULL AND o.Agents <> 'NaN'
-- the same player name can appear twice in one map when two different people share it:
QUALIFY count(*) OVER (PARTITION BY m.match_map_id, p.player_id) = 1;

-- One row per agent a team played on a map, with the map result. Built from the player
-- rows for every year, so 2021-2026 share one shape (the raw team-comp file changed
-- format in 2024).
CREATE OR REPLACE TABLE fact_team_comp AS
SELECT
    f.match_map_id                          AS game_id,
    m.event_id,
    m.year,
    m.map_name,
    f.team_id,
    CASE WHEN f.team_id = m.team_a_id THEN m.team_b_id ELSE m.team_a_id END AS opponent_id,
    CASE WHEN m.winner_team_id = f.team_id THEN 'win'
         WHEN m.winner_team_id IS NULL THEN 'draw' ELSE 'loss' END        AS result,
    f.agent_name
FROM fact_player_map f
JOIN fact_map_result m USING (match_map_id);
