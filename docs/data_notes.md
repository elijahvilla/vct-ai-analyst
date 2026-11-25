# Data notes

**Source:** Kaggle, "Valorant Champion Tour 2021–2026 Data" by Ryan Luong
(https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data), scraped from vlr.gg.
**License:** MIT. Redistribution is allowed with the license and credit; this repo credits the dataset author and vlr.gg.

**Coverage:** 134 CSV files, about 1.5 GB, seasons 2021–2026, one folder per year plus `all_ids/`.
2021 has 142 events (every Challengers qualifier); 2022 has 58; 2023–2026 have 10–15 each (the partnered
international league era). `dim_event.is_international` marks top-tier events so questions can filter.

## Traps found while profiling

1. **Side rows triple-count.** `overview.csv` has every player-map three times: `Side = both`, `attack`, `defend`.
   Summing without `Side = 'both'` triples every number. Handled in `fact_player_map`.
2. **Rollup rows.** Some files include `Map = 'All Maps'` or `Agent = 'All Agents'` summary rows. Dropped.
3. **Percentages are text.** KAST and headshot % are stored as `"81%"`. Converted to numbers on a 0–100 scale.
4. **Agent name casing.** `overview.csv` uses lowercase (`jett`, `kayo`); the team-comp file uses `Jett`.
   The database uses lowercase everywhere; KAY/O is stored as `kayo`.
5. **The team-comp file changed format in 2024.** 2021–2023: season totals per team and agent. 2024+: one row per
   game with five agent columns. Instead of stitching both, `fact_team_comp` is built from the player rows for every year.
6. **Commas inside names.** A team is called "Stay Small, Stay Second"; the loader always honors quoted fields.
7. **Repeated keys.** A few series play the same map twice, and a few player names belong to two different people
   in the same map. Those rows can't be matched safely and are dropped: `fact_player_map` keeps 272,714 of 280,032
   player-map rows (97.4%).
8. **Players have no IDs in the stats file.** `dim_player` is keyed by name, so two people with the same name are
   merged across matches. Known limitation.
9. **Encoding.** Some 2021–2022 event names show `Reykjav�k` (the source file's encoding); left as-is.

## Row counts (after build)

| Table | Rows |
|---|---|
| dim_event | 250 |
| dim_team | 3,998 |
| dim_player | 15,399 |
| dim_agent | 29 |
| dim_map | 13 |
| fact_map_result | 27,394 |
| fact_player_map | 272,714 |
| fact_team_comp | 272,714 |
