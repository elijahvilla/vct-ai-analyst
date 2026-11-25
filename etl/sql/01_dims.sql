-- 01_dims.sql — dimension tables (one row per thing) built from the raw views.
-- Run by etl/build_db.py after it registers raw_* views. Facts are in 02_facts.sql.

-- Events (tournaments). One ID per tournament name + year.
-- is_international: 2023+ is the partnered league era (all top tier);
-- before 2023 only Masters (international) and Valorant Champions count.
CREATE OR REPLACE TABLE dim_event AS
SELECT
    min("Tournament ID")::BIGINT AS event_id,
    Tournament                   AS event_name,
    Year::INTEGER                AS year,
    (Year >= 2023
     OR Tournament ILIKE 'Valorant Champions 20%'
     OR Tournament ILIKE 'Valorant Champions Tour Stage%Masters%') AS is_international
FROM raw_all_all_tournaments_stages_match_types_ids
GROUP BY Tournament, Year;

-- Maps: every real map that appears in map results (no 'All Maps' rollup).
CREATE OR REPLACE TABLE dim_map AS
SELECT DISTINCT Map AS map_name
FROM raw_maps_scores
WHERE Map IS NOT NULL AND Map <> 'All Maps';

-- Teams: every team name seen in map results or player rows. Surrogate IDs because
-- the raw player rows only carry names.
CREATE OR REPLACE TABLE dim_team AS
WITH names AS (
    SELECT "Team A" AS team_name FROM raw_maps_scores
    UNION SELECT "Team B" FROM raw_maps_scores
    UNION SELECT Team FROM raw_overview
)
SELECT dense_rank() OVER (ORDER BY team_name)::INTEGER AS team_id, team_name
FROM names
WHERE team_name IS NOT NULL;

-- Players: keyed by name (the overview file has no player IDs, and a few names repeat
-- across different people — a known limitation recorded in docs/data_notes.md).
CREATE OR REPLACE TABLE dim_player AS
SELECT dense_rank() OVER (ORDER BY player_name)::INTEGER AS player_id, player_name
FROM (SELECT DISTINCT Player AS player_name FROM raw_overview WHERE Player IS NOT NULL);

-- Agents and roles: written by hand (the data has no roles). Names lowercase to match
-- raw_overview ('kayo' is KAY/O).
CREATE OR REPLACE TABLE dim_agent AS
SELECT * FROM (VALUES
    ('jett', 'duelist'), ('raze', 'duelist'), ('reyna', 'duelist'), ('phoenix', 'duelist'),
    ('yoru', 'duelist'), ('neon', 'duelist'), ('iso', 'duelist'), ('waylay', 'duelist'),
    ('sova', 'initiator'), ('breach', 'initiator'), ('skye', 'initiator'), ('kayo', 'initiator'),
    ('fade', 'initiator'), ('gekko', 'initiator'), ('tejo', 'initiator'),
    ('omen', 'controller'), ('brimstone', 'controller'), ('viper', 'controller'),
    ('astra', 'controller'), ('harbor', 'controller'), ('clove', 'controller'),
    ('killjoy', 'sentinel'), ('cypher', 'sentinel'), ('sage', 'sentinel'), ('chamber', 'sentinel'),
    ('deadlock', 'sentinel'), ('vyse', 'sentinel'), ('veto', 'sentinel'),
    ('miks', NULL)  -- TODO(owner): Miks' role — confirm before the build is final
) AS t(agent_name, role);
