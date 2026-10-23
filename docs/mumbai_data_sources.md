# Mumbai source catalogue

This page records the Mumbai-specific source mapping used by the pipeline.
It complements the concise inventory in
[data_sources.md](data_sources.md); it does not describe another city or an
independent dataset.

## Dataset mapping

| ID | Dataset or input | Repository evidence | Use |
| --- | --- | --- | --- |
| DS-01 | 500 m grid | `data/processed/grids/mumbai_grid_500m.geojson` | Grid inference and map display. |
| DS-02 | Static spatial features | `data/processed/features/mumbai_static_spatial_features.parquet` | Model predictors. |
| DS-03 | Elevation cache | `backend/data/mumbai/raw/mumbai_dem_elevations.json` when present | DEM-derived elevation features. |
| DS-04 | Microwatersheds | `backend/data/mumbai/raw/mumbai_microwatersheds.geojson` when present | Drainage and watershed features. |
| DS-05 | Critical infrastructure | `data/processed/vectors/mumbai_critical_infrastructure.parquet` | Hospital, fire, and police proximity/accessibility. |
| DS-06 | Chronic waterlogging labels | Constants and label construction in `scripts/build_mumbai_pipeline.py` | 750 m proximity proxy for model training. |
| DS-07 | OSM drive graph | `data/processed/roads/mumbai_drive_network.json.gz` | Cached road routing and network analysis. |
| DS-08 | Rainfall scenarios | Horizon logic in `backend/app/services/flood_service.py` | Deterministic inference forcing, not live telemetry. |
| DS-09 | XGBoost model | `models/trained/mumbai_xgboost_baseline.json` | Prototype susceptibility scoring. |

Availability of raw files is build-dependent. Do not treat a listed optional
cache as proof that it is present in every checkout.

## Referenced portals and licences

The provenance manifest records the sources verified for the current generated
assets, including OpenCity Mumbai, MRSAC/OpenCity microwatersheds, Copernicus
DEM access, and the BMC Disaster Management chronic-waterlogging reference.
OpenStreetMap road data is downloaded through Overpass and is distributed under
the ODbL. Consult the manifest and generated cache metadata for the exact
status of each local asset before relying on it.

## Guardrails

1. The project is Mumbai-only; Chennai datasets, loaders, and experimental DNO
   material are not active components.
2. Water depth is unmeasured and must remain `null`.
3. Model metrics describe agreement with the BMC hotspot-proximity proxy, not
   calibrated flood probability or event forecasting.
4. Road routing is a cached OSM network, not live traffic or a closure
   advisory.
5. Rainfall endpoints are labelled scenario/demo unless a separate live feed
   is explicitly wired and verified.
