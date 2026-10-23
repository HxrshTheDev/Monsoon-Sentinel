# Active component audit

**Status:** Historical context retained for maintainers. The active application
is Mumbai-only.

## Active reusable components

| Component | Path | Role |
| --- | --- | --- |
| Mumbai grid | `data/processed/grids/mumbai_grid_500m.geojson` | Grid inference and map display. |
| Mumbai static features | `data/processed/features/mumbai_static_spatial_features.parquet` | Model predictors. |
| Mumbai infrastructure | `data/processed/vectors/mumbai_critical_infrastructure.parquet` | Facility exposure and accessibility. |
| Mumbai XGBoost model | `models/trained/mumbai_xgboost_baseline.json` | Prototype susceptibility scoring. |
| FastAPI services | `backend/app/services/` | Inference, routing, accessibility, and prioritization. |
| Angular SPA | `Frontend/` | Dashboard, map, EOC, analytics, and routing views. |

## Explicitly out of scope

- Chennai grid, parquet, booster, or loader artifacts.
- Chennai DNO hydrodynamic experiments.
- Claims that the default rainfall payload is live AWS/IMD telemetry.
- Fabricated continuous water-depth values.

## Schema legacy

The feature column `dist_to_buckingham_canal_m` is retained for model-schema
compatibility. In this Mumbai dataset it stores distance to the Mithi/Mahim
Creek corridor. See [data_sources.md](data_sources.md) for the broader
provenance inventory.
