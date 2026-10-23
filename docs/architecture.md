# Monsoon Sentinel architecture

This document describes the active Mumbai implementation. It is an evidence
based overview of the repository, not a claim that the prototype is a live
flood-warning or hydrodynamic system.

## System flow

```mermaid
flowchart LR
    A[Data Sources] --> B[Geospatial Processing]
    B --> C[Risk Model]
    C --> D[FastAPI Backend]
    D --> E[Angular Frontend]
    D --> F[Decision Support]
    E --> F
```

### Components

| Layer | Repository evidence | Responsibility |
| --- | --- | --- |
| Data sources | `backend/data/mumbai/raw/`, `data/processed/` | Stores downloaded/cached Mumbai source data and derived assets. |
| Geospatial processing | `scripts/build_mumbai_pipeline.py`, `scripts/build_mumbai_road_network.py` | Builds the 500 m grid, static features, infrastructure data, and OSM road cache. |
| Risk model | `backend/app/services/flood_service.py`, `models/trained/mumbai_xgboost_baseline.json` | Scores grid cells using the XGBoost model blended with a transparent susceptibility calculation. |
| FastAPI backend | `backend/app/main.py`, `backend/app/api/` | Loads data/services and exposes `/api/v1` REST routes. |
| Angular frontend | `Frontend/src/` | Presents maps, routing, EOC, analytics, and decision-support views. |
| Decision support | `backend/app/services/accessibility_service.py`, `prioritization_service.py`, `road_network_service.py` | Compares accessibility, network criticality, routes, and inspection priorities under scenario assumptions. |

## Runtime path

1. `backend.app.main` initializes the data loader, flood service, and road
   network service during application startup.
2. `DataLoaderService` validates the checked-in/generated Mumbai assets and
   exposes infrastructure and spatial data.
3. `FloodService` loads the XGBoost booster and static features. Forecast
   horizons use deterministic rainfall baselines (`NOW`, `+30M`, `+1H`,
   `+2H`, and `+3H`); they are not live observations.
4. `RoadNetworkService` loads the cached OSM graph and samples susceptibility
   along real edge geometry. Missing or unknown risk is reported and
   penalized; route coordinates returned by the API are `[latitude, longitude]`.
5. Accessibility and prioritization services use the road graph and flood
   susceptibility to calculate scenario comparisons.
6. The Angular application calls the REST API using the development base URL in
   `Frontend/src/environments/environment.ts`.

## Data and model facts

- The provenance manifest records 1,767 grid cells, 537 infrastructure records,
  and 25 model feature columns.
- The checked-in evaluation metadata reports accuracy `0.981`, F1 `0.929`,
  and ROC-AUC `0.995`. These metrics measure agreement with the BMC
  hotspot-proximity proxy under stratified cross-validation; they are not
  calibrated event-forecasting metrics.
- `waterDepth` is explicitly `null` because continuous depth is not measured.
- The road-cache metadata records 71,590 nodes and 96,230 edges for its
  arterial/collector download. These counts can change when the cache is
  rebuilt.
- The legacy feature name `dist_to_buckingham_canal_m` is retained for schema
  compatibility and represents the Mithi/Mahim Creek corridor distance in this
  Mumbai dataset.

## API surface

The route groups are registered in `backend/app/api/api_router.py`:

| Group | Representative routes |
| --- | --- |
| Health | `/health`, `/health/system-overview` |
| Flood susceptibility | `/current-risk/kpis`, `/forecast-risk`, `/hotspots`, `/map-data/zones/{grid_id}` |
| Routing | `/safe-route`, `/safe-route/presets` |
| Criticality | `/criticality/roads`, `/criticality/network-overview` |
| Accessibility | `/accessibility/analysis`, `/accessibility/facilities` |
| Prioritization | `/prioritization/rank`, `/prioritization/compare` |
| Analytics | `/analytics/summary`, `/analytics/decision-report` |

See [API.md](API.md) for request and response details.

## Boundaries and limitations

- Data and model outputs are Mumbai-specific; no Chennai assets or active
  loaders belong to this project.
- Scenario rainfall and road disruption outputs are decision-support
  simulations, not official advisories.
- OSM routing is a cached network and does not provide live traffic or verified
  road closures.
- Source, license, and provenance notes are maintained in
  [data_sources.md](data_sources.md) and
  [mumbai_data_sources.md](mumbai_data_sources.md).
