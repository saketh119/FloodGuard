# Dataset Analysis

Do not clean the data yet. This document records the first-pass audit for each CSV in `datasets/raw/ml/`.

| Dataset | Rows | Columns | Target Variable | Missing Values | Duplicates | Comments |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| flood_risk_india.csv | 10000 | 14 | Flood risk / target label (confirm column name in notebook) | 0 | 0 | Balanced first-pass shape; no missing values or duplicates detected. |
| indian_rainfall_daily_measurements.csv | 8790 | 1 | Daily rainfall measurement | 0 | 0 | Single-column time series-style dataset. |
| indofloods_flood_events.csv | 4548 | 13 | Flood event outcome / event label (confirm column name in notebook) | 1687 | 0 | Contains substantial missingness and needs careful exploration before any cleaning. |
| indofloods_precipitation_variables.csv | 4548 | 11 | Precipitation variables / feature set | 0 | 0 | Appears complete at first pass. |
| indofloods_catchment_characteristics.csv | 155 | 108 | Catchment characteristics / feature set | 3112 | 0 | Wide table with many missing values; likely requires feature-by-feature review. |

## Notes

- Inspect each dataset with `head`, `info`, `describe`, `shape`, `columns`, `isnull().sum()`, and `duplicated().sum()` before removing anything.
- Keep raw datasets untouched until the exploration notebook identifies which fields matter for modeling.
