-- Tiny copy of the real schema for fast tests (same tables/columns as etl/sql).
CREATE TABLE dim_event (event_id INTEGER, event_name TEXT, year INTEGER, is_international BOOLEAN);
INSERT INTO dim_event VALUES (2097, 'Valorant Champions 2024', 2024, true), (1999, 'Champions Tour 2024: Americas Stage 1', 2024, true);
CREATE TABLE dim_team (team_id INTEGER, team_name TEXT);
INSERT INTO dim_team VALUES (1, 'Sentinels'), (2, 'Gen.G'), (3, 'FNATIC');
CREATE TABLE dim_player (player_id INTEGER, player_name TEXT);
INSERT INTO dim_player VALUES (1, 'TenZ'), (2, 'zekken'), (3, 't3xture'), (4, 'Boaster');
CREATE TABLE dim_agent (agent_name TEXT, role TEXT);
INSERT INTO dim_agent VALUES ('jett', 'duelist'), ('kayo', 'initiator'), ('sova', 'initiator'), ('omen', 'controller');
CREATE TABLE dim_map (map_name TEXT);
INSERT INTO dim_map VALUES ('Ascent'), ('Bind');
CREATE TABLE fact_map_result (match_map_id INTEGER, event_id INTEGER, year INTEGER, stage TEXT, match_type TEXT,
  match_name TEXT, map_name TEXT, team_a_id INTEGER, team_b_id INTEGER, winner_team_id INTEGER,
  team_a_score INTEGER, team_b_score INTEGER, went_overtime BOOLEAN, duration TEXT);
INSERT INTO fact_map_result VALUES
  (1, 2097, 2024, 'Group Stage', 'Opening (B)', 'Gen.G vs Sentinels', 'Ascent', 2, 1, 2, 13, 7, false, '46:45'),
  (2, 2097, 2024, 'Group Stage', 'Opening (B)', 'Gen.G vs Sentinels', 'Bind', 2, 1, 1, 9, 13, false, '50:02'),
  (3, 1999, 2024, 'Playoffs', 'Upper Final', 'FNATIC vs Sentinels', 'Ascent', 3, 1, 3, 14, 12, true, '61:10');
CREATE TABLE fact_player_map (match_map_id INTEGER, player_id INTEGER, team_id INTEGER, agent_name TEXT,
  rating DOUBLE, acs INTEGER, kills INTEGER, deaths INTEGER, assists INTEGER, kast_pct DOUBLE, adr INTEGER,
  headshot_pct DOUBLE, first_kills INTEGER, first_deaths INTEGER);
INSERT INTO fact_player_map VALUES
  (1, 1, 1, 'jett', 1.05, 230, 18, 15, 3, 72, 150, 28, 4, 3),
  (1, 2, 1, 'sova', 0.95, 190, 14, 16, 6, 68, 130, 22, 1, 2),
  (1, 3, 2, 'jett', 1.60, 305, 24, 12, 4, 81, 188, 31, 3, 4),
  (2, 1, 1, 'jett', 1.20, 250, 20, 14, 2, 75, 160, 30, 5, 2),
  (2, 3, 2, 'omen', 0.90, 180, 12, 17, 7, 66, 120, 20, 1, 3),
  (3, 1, 1, 'kayo', 1.10, 210, 17, 16, 9, 77, 140, 25, 2, 2),
  (3, 4, 3, 'omen', 0.85, 160, 11, 18, 10, 70, 110, 18, 0, 1);
CREATE TABLE fact_team_comp AS
  SELECT f.match_map_id AS game_id, m.event_id, m.year, m.map_name, f.team_id,
         CASE WHEN f.team_id = m.team_a_id THEN m.team_b_id ELSE m.team_a_id END AS opponent_id,
         CASE WHEN m.winner_team_id = f.team_id THEN 'win' ELSE 'loss' END AS result, f.agent_name
  FROM fact_player_map f JOIN fact_map_result m USING (match_map_id);
