# CityPulse / Monsoon Sentinel

Mumbai-focused flood **susceptibility** and disruption decision support for
Brihanmumbai Municipal Corporation (BMC / MCGM).

The repository contains a FastAPI backend, an Angular frontend, a Mumbai
geospatial/model pipeline, and tests. Scores are prototype susceptibility
estimates under scenario rainfall; they are **not calibrated probabilities of
a future flood**. Continuous water depth is unmeasured and is returned as
`null`.

## Scope and evidence

- Study area: Greater Mumbai, approximately `18.89-19.30 N` and
  `72.75-73.02 E`.
- Metric CRS: `EPSG:32643`; web/GeoJSON CRS: `EPSG:4326`.
- Model labels: proximity to BMC chronic waterlogging hotspot coordinates
  within 750 m.
- Road graph: OpenStreetMap highway geometry downloaded through Overpass.
- Rainfall: deterministic scenario baselines in the default demo, not live
  IMD or BMC AWS observations.

See [the architecture and data flow](docs/architecture.md), [the API
reference](docs/API.md), and [data provenance](docs/data_sources.md) for
implementation details.

## Repository layout

```text
config.py                 Shared Mumbai settings and paths
backend/app/              FastAPI application and services
Frontend/                 Angular SPA
data/processed/           Generated grid, features, infrastructure, and roads
models/trained/           Trained XGBoost model and evaluation metadata
scripts/                  Mumbai data, road-network, and model commands
tests/                    pytest integration and service tests
docs/                     Architecture, API, provenance, and audit notes
```

## Prerequisites

- Python 3.11 or 3.12 (64-bit)
- Node.js 20 or later and npm 10 or later
- Git

## Run the backend

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is available at `http://localhost:8000`. Swagger UI is at
`/docs`, ReDoc is at `/redoc`, and the health endpoint is
`/api/v1/health`.

## Run the frontend

In a second terminal:

```powershell
cd Frontend
npm install
npm start
```

Open `http://localhost:4200/`. The development environment uses the real API
(`useMockData: false`) with a default base URL of `http://localhost:8000`.

The main UI paths include `/dashboard`, `/flood-map`, `/safe-route`, `/eoc`,
and `/analytics`. Demo login role buttons are available when the authentication
API is offline.

## Data and model assets

The default demo expects these generated or checked-in assets:

- `data/processed/grids/mumbai_grid_500m.geojson`
- `data/processed/features/mumbai_static_spatial_features.parquet`
- `data/processed/vectors/mumbai_critical_infrastructure.parquet`
- `data/processed/roads/mumbai_drive_network.json.gz`
- `models/trained/mumbai_xgboost_baseline.json`

The full asset inventory, source status, CRS, labels, and routing assumptions
are maintained in [docs/data_sources.md](docs/data_sources.md) and
[docs/mumbai_data_sources.md](docs/mumbai_data_sources.md).

## Rebuild or retrain

Run from the repository root:

```powershell
# Rebuild the Mumbai GIS pipeline.
python scripts/build_mumbai_pipeline.py

# Download/build the cached OSM road graph.
python scripts/build_mumbai_road_network.py

# Retrain the model from the existing Mumbai feature dataset.
python scripts/retrain_mumbai_model.py
```

The GIS and road commands may require network access. Rebuild outputs are
written under `data/processed/`; raw downloads, when available, are kept
under `backend/data/mumbai/raw/`.

## Test

```powershell
pytest tests -v
```

The tests exercise API responses, data validation, flood inference,
prioritization, accessibility, road criticality, and route geometry. Tests
that require a road cache may skip when that cache is absent.

## Environment

`.env.example` documents the supported settings. Common overrides include:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Application/JWT secret; replace the development default for deployment |
| `ENVIRONMENT` | Runtime environment, such as `development` or `production` |
| `MODEL_PATH` | Trained model path |
| `GRID_GEOJSON_PATH` | Mumbai grid path |
| `STATIC_FEATURES_PATH` | Static feature parquet path |
| `CRITICAL_INFRA_PATH` | Infrastructure parquet path |
| `ROAD_NETWORK_PATH` | OSM road-cache path |

## Limitations

- The default rainfall and telemetry payloads are labelled scenario/demo data.
- The model is evaluated against a BMC hotspot-proximity proxy, not
  chronological flood-event labels or calibrated flood probabilities.
- Water depth is unmeasured and remains `null`.
- Routing uses cached OSM geometry and configured road classes; it is not live
  traffic, closure, or emergency advice.
- Optional feeds are not assumed to be present.

For the retained historical component audit, see
[docs/reference_component_audit.md](docs/reference_component_audit.md).
