# Reference Component Audit (Mumbai-only active project)

**Status:** Historical audit notes retained for context. **Active application is Mumbai-only.**

Chennai grid/features/infrastructure/model artifacts and DNO phase docs were removed from the active tree. Do not restore Chennai datasets or loaders.

## Active reusable components

| Component | Path | Role |
|---|---|---|
| Mumbai 500m grid | `data/processed/grids/mumbai_grid_500m.geojson` | Inference / map tiles |
| Mumbai static features | `data/processed/features/mumbai_static_spatial_features.parquet` | 25 predictors |
| Mumbai infrastructure | `data/processed/vectors/mumbai_critical_infrastructure.parquet` | Facilities |
| Mumbai XGBoost | `models/trained/mumbai_xgboost_baseline.json` | Prototype susceptibility |
| FastAPI services | `backend/app/services/*` | Inference, routing, accessibility, prioritization |
| Angular SPA | `Frontend/` | Dashboard, map, EOC, routing UI |

## Intentionally excluded from active use

- Any Chennai grid / parquet / booster artifacts
- Chennai DNO hydrodynamic experimental services
- Claims of live AWS rainfall or fabricated water depth

## Unavoidable schema legacy

- Feature column `dist_to_buckingham_canal_m` is retained for model schema compatibility and stores **Mithi / Mahim Creek corridor** distance for Mumbai cells.
