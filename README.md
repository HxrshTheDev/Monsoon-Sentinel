# CityPulse / Monsoon Sentinel

[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Angular](https://img.shields.io/badge/Angular-21-dd0031.svg)](https://angular.dev/)
[![Challenge](https://img.shields.io/badge/Hackathon-HackAMatch%201.0%20(CityPulse)-orange.svg)]()

Mumbai-only flood **susceptibility** and disruption decision-support prototype for **Brihanmumbai Municipal Corporation (BMC / MCGM)**.

**Team:** Omkar Musale (Team Leader), Tanvi Gawade, Harsh Gosavi  
**Geography:** Greater Mumbai ($18.89^\circ$–$19.30^\circ$ N, $72.75^\circ$–$73.02^\circ$ E)  
**CRS:** `EPSG:32643` (metric) · `EPSG:4326` (map / GeoJSON)

> Scores are **prototype susceptibility estimates** under scenario rainfall. They are **not** calibrated probabilities of a future flood. Water depth is unmeasured (`null`) and never fabricated.

---

## Repository layout

```text
monsoon-sentinel/
├── config.py                 # Shared settings (Mumbai paths, bounds, CORS)
├── requirements.txt
├── .env.example
├── backend/app/              # FastAPI application
├── Frontend/                 # Angular 21 SPA
├── data/processed/           # Mumbai grid, features, infrastructure
├── models/trained/           # mumbai_xgboost_baseline.json (+ evaluation JSON)
├── scripts/                  # GIS pipeline + model retrain
├── tests/                    # pytest suite
└── docs/                     # Architecture & data provenance
```

---

## Prerequisites (Windows-friendly)

- Python 3.11 or 3.12 (64-bit)
- Node.js 20+ and npm 10+
- Git

---

## 1. Backend setup

```powershell
cd C:\path\to\monsoon-sentinel
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Start API

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

| Resource | URL |
|---|---|
| API root | http://localhost:8000/ |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health | http://localhost:8000/api/v1/health |

### Key endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Health |
| GET | `/api/v1/health/system-overview` | Diagnostics + honest model caveats |
| GET | `/api/v1/current-risk/kpis` | Scenario KPIs |
| GET | `/api/v1/forecast-risk?horizon=NOW` | 500m susceptibility grid |
| GET | `/api/v1/hotspots?limit=20` | Ranked hotspots |
| POST | `/api/v1/safe-route` | OSM road-network flood-aware routing |
| GET | `/api/v1/criticality/roads` | Betweenness / bridges |
| GET | `/api/v1/accessibility/analysis` | Emergency accessibility |
| POST | `/api/v1/prioritization/rank` | Inspection ranking |
| POST | `/api/v1/prioritization/compare?budget_k=5` | Strategy A vs B |
| GET | `/api/v1/analytics/decision-report` | Executive report |

---

## 2. Frontend setup

```powershell
cd Frontend
npm install
npm start
```

Open **http://localhost:4200/**

- Dev API base: `http://localhost:8000` (`Frontend/src/environments/environment.ts`)
- `useMockData` is **false** — the UI calls the real FastAPI backend
- Demo login: use the demo role buttons on `/login` if the auth API is offline

### Main journey

1. Landing → Login (demo roles) or open `/dashboard` / `/flood-map`
2. Inspect Mumbai susceptibility map and hotspots
3. Change forecast horizon where offered
4. `/safe-route` for OSM road-following flood-aware routing
5. `/eoc` for Emergency Operations Centre (backend hotspots + labelled simulation)
6. `/analytics` for reports; prioritization via API / dashboard widgets

---

## 3. Data & model

Expected runtime assets (already in repo for demo):

- `data/processed/grids/mumbai_grid_500m.geojson`
- `data/processed/features/mumbai_static_spatial_features.parquet`
- `data/processed/vectors/mumbai_critical_infrastructure.parquet`
- `data/processed/roads/mumbai_drive_network.json.gz` (OSM road cache)
- `models/trained/mumbai_xgboost_baseline.json`

Regenerate / retrain:

```powershell
# Full GIS rebuild (uses cached raw under backend/data/mumbai/raw when present)
python scripts/build_mumbai_pipeline.py

# OSM road network for Safe Route (Overpass; writes the gzip cache above)
python scripts/build_mumbai_road_network.py

# Retrain only (fixes label leakage; writes evaluation JSON)
python scripts/retrain_mumbai_model.py
```

**Labels:** BMC chronic waterlogging hotspot proximity (750 m), not a circular hazard formula.  
**Road graph:** OpenStreetMap drive highways (arterial/collector) for the Mumbai study bbox — see `docs/data_sources.md`.

---

## 4. Tests

```powershell
pytest tests -v
```

---

## 5. Environment variables

See `.env.example`. Minimum:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT / app secret (required for any non-dev deploy) |
| `ENVIRONMENT` | `development` / `production` |
| `MODEL_PATH` | Override trained model path |
| `GRID_GEOJSON_PATH` | Override Mumbai grid path |
| `STATIC_FEATURES_PATH` | Override features parquet |
| `CRITICAL_INFRA_PATH` | Override infrastructure parquet |

CORS defaults to local Angular/Vite origins (no wildcard).

---

## 6. Known limitations

- No live IMD/BMC AWS rainfall feed in the default demo (scenario baselines + labelled simulation).
- No continuous water-depth model — depth stays `null`.
- Model metrics describe agreement with hotspot-proximity labels, not operational flood forecasting skill.
- Road routing covers curated corridors only.
- EOC drainage / radar layers fall back to clearly labelled simulation when optional feeds are absent.

Further provenance: `docs/data_sources.md`, `docs/mumbai_data_sources.md`, `docs/architecture.md`.
