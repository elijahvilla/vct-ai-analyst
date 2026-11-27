-- 03_metrics.sql — ready-made metrics with the tricky math done once, correctly.
-- The AI is told to prefer these tables, so it doesn't re-derive pick and win rates each time.

-- One row per event + map + agent.
--   team_maps        times a team played the agent on that map (both teams picking it = 2)
--   maps_with_agent  maps where at least one team played it (both teams picking it = 1)
--   maps_played      maps played on that map at that event
CREATE OR REPLACE TABLE metric_agent_event_map AS
WITH maps AS (
    SELECT event_id, year, map_name, count(*) AS maps_played
    FROM fact_map_result GROUP BY ALL
), picks AS (
    SELECT event_id, map_name, agent_name,
           count(DISTINCT (game_id, team_id))                                   AS team_maps,
           count(DISTINCT (game_id, team_id)) FILTER (WHERE result = 'win')     AS team_maps_won,
           count(DISTINCT game_id)                                              AS maps_with_agent
    FROM fact_team_comp GROUP BY ALL
),
-- every agent gets a row for every event + map (0 picks where unused), so summing maps_played
-- over any set of an agent's rows always gives the true number of maps
event_agents AS (
    SELECT DISTINCT m.event_id, a.agent_name FROM fact_map_result m CROSS JOIN dim_agent a
)
SELECT m.event_id, m.year, m.map_name, ea.agent_name, a.role,
       coalesce(p.team_maps, 0)       AS team_maps,
       coalesce(p.team_maps_won, 0)   AS team_maps_won,
       coalesce(p.maps_with_agent, 0) AS maps_with_agent,
       m.maps_played,
       round(100.0 * coalesce(p.team_maps, 0) / (2 * m.maps_played), 1)       AS pick_rate_pct,
       round(100.0 * p.team_maps_won / nullif(p.team_maps, 0), 1)             AS win_rate_pct
FROM maps m
JOIN event_agents ea USING (event_id)
JOIN dim_agent a ON a.agent_name = ea.agent_name
LEFT JOIN picks p ON p.event_id = m.event_id AND p.map_name = m.map_name AND p.agent_name = ea.agent_name;

-- One row per event + map + team.
CREATE OR REPLACE TABLE metric_team_event_map AS
WITH sides AS (
    SELECT event_id, year, map_name, team_a_id AS team_id, (winner_team_id = team_a_id)::INT AS won FROM fact_map_result
    UNION ALL
    SELECT event_id, year, map_name, team_b_id, (winner_team_id = team_b_id)::INT FROM fact_map_result
)
SELECT event_id, year, map_name, team_id,
       count(*) AS maps_played, sum(won) AS maps_won,
       round(100.0 * sum(won) / count(*), 1) AS win_rate_pct
FROM sides GROUP BY ALL;

-- One row per event + player + team.
CREATE OR REPLACE TABLE metric_player_event AS
SELECT m.event_id, m.year, f.player_id, f.team_id,
       count(*)                     AS maps_played,
       sum(f.kills)                 AS kills,
       sum(f.deaths)                AS deaths,
       sum(f.assists)               AS assists,
       sum(f.first_kills)           AS first_kills,
       round(avg(f.rating), 2)      AS avg_rating,
       round(avg(f.acs), 1)         AS avg_acs
FROM fact_player_map f
JOIN fact_map_result m USING (match_map_id)
GROUP BY ALL;
