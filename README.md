# CityPulse — Urban Flood Disruption & Decision-Support System

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Tests Passing](https://img.shields.io/badge/pytest-32%20passed-brightgreen.svg)](tests/)
[![Challenge](https://img.shields.io/badge/Hackathon-HackAMatch%201.0%20(CityPulse)-orange.svg)]()

A high-resolution flood-disruption decision-support backend for **Brihanmumbai Municipal Corporation (BMC / MCGM)** and contiguous Mumbai metropolitan urban catchments ($18.89^\circ - 19.30^\circ\text{ N}, 72.75^\circ - 73.02^\circ\text{ E}$).

CityPulse integrates **empirical flood susceptibility evidence** with **road-network graph criticality** to evaluate essential-service accessibility degradation and optimize resource-constrained interventions (e.g. mobile dewatering pumps, inspection crews, and temporary barriers) under finite municipal budgets.

---

## 1. Key Analytical Features

- **XGBoost Flood Susceptibility Engine**: Vectorized forward pass across 1,767 terrestrial 500m x 500m cells (`EPSG:32643` / `EPSG:4326`) using 25 audited meteorological, topographical, drainage, and land-use predictors. Retrained with 5-fold cross-validation achieving **0.972 Accuracy**, **0.949 F1-score**, and **0.997 ROC-AUC**.
- **Road Network Graph & Criticality**: NetworkX directed multigraph modeling 25 nodes and 29 arterial links across Greater Mumbai (Western Express Highway, Eastern Express Highway, Bandra-Worli Sea Link, Eastern Freeway elevated viaducts, Mahim Causeway, SCLR, JVLR, and subways). Calculates edge betweenness centrality, degree centrality, and detects single-point-of-failure bridges/cut-edges.
- **Essential-Service Accessibility Assessment**: Shortest-path routing from 8 residential population clusters (Kurla, Sion, Hindmata, Andheri, Bandra, Chembur, Malad, Borivali) to tertiary trauma hospitals (KEM, Sion, Lilavati, Kokilaben), fire headquarters, and police command hubs under baseline vs flood-disrupted conditions.
- **Transparent Inspection Prioritization**: Multi-criteria decision analysis combining flood hazard, network betweenness, accessibility delay impact, and facility exposure with explainable formulas.
- **Resource-Constrained Scenario Simulation**: Evaluates **Strategy A (Hazard-Only)** vs **Strategy B (Network-Aware)** under budget $K$, quantifying critical bridges safeguarded, emergency delay minutes mitigated, and facilities preserved from isolation.
- **Scientific Integrity Guardrails**: Continuous hydrodynamic water depth is unmeasured and **not fabricated** (`waterDepth: null`). Disrupted roads are decision-support simulations, **not** operational emergency warnings.

---

## 2. Target Directory Structure

```text
urban-floos-/
├── config.py                          # Application settings & environment configuration
├── requirements.txt                   # Dependency declarations
├── .gitignore                         # Python/data ignore rules
├── README.md                          # Project documentation
├── docs/                              # Technical and audit deliverables
│   ├── reference_component_audit.md   # Reference repository component audit
│   ├── architecture.md                # System architecture and data flow
│   ├── data_sources.md                # Ingested datasets, CRS, and provenance
│   ├── integration_report.md          # Inventory of integrated & excluded files
│   └── test_report.md                 # Reproducible test specifications

├── data/                              # Verified geospatial assets
│   └── processed/
│       ├── grids/
│       │   ├── mumbai_grid_500m.geojson      (1,767 cells, EPSG:32643 - ACTIVE)
│       │   └── chennai_grid_500m.geojson     (3,963 cells, EPSG:32644 - PRESERVED)
│       ├── features/
│       │   ├── mumbai_static_spatial_features.parquet (1,767 rows, 25 predictors - ACTIVE)
│       │   └── chennai_static_spatial_features.parquet (3,963 rows, 25 predictors - PRESERVED)
│       └── vectors/
│           ├── mumbai_critical_infrastructure.parquet (162 facilities, EPSG:32643 - ACTIVE)
│           └── chennai_critical_infrastructure.parquet (1,505 facilities - PRESERVED)
├── models/
│   └── trained/
│       ├── mumbai_xgboost_baseline.json      (Retrained Mumbai booster - ACTIVE)
│       └── chennai_xgboost_baseline.json     (Chennai booster - PRESERVED)
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI application & lifespan setup
│       ├── core/config.py             # Config proxy
│       ├── schemas/                   # Pydantic v2 data models
│       │   ├── provenance.py          # Observation status tracking
│       │   ├── flood.py               # Flood zones and KPIs
│       │   ├── hotspot.py             # Hotspots and honest depth
│       │   ├── route.py               # Route planning
│       │   ├── criticality.py         # Network betweenness and bridges
│       │   ├── accessibility.py       # Baseline vs disrupted travel times
│       │   ├── prioritization.py      # Multi-criteria ranking and budget K
│       │   └── analytics.py           # Executive report schemas
│       ├── services/                  # Analytical business logic
│       │   ├── data_loader_service.py # Schema & coordinate validation
│       │   ├── flood_service.py       # XGBoost inference
│       │   ├── road_network_service.py# NetworkX graph & Dijkstra routing
│       │   ├── accessibility_service.py# Emergency facility accessibility
│       │   └── prioritization_service.py# Inspection ranking & scenario budget
│       └── api/
│           ├── api_router.py          # Router aggregator
│           └── routes/                # Modular REST endpoints
│               ├── health.py
│               ├── flood.py
│               ├── routing.py
│               ├── criticality.py
│               ├── accessibility.py
│               ├── prioritization.py
│               └── analytics.py
└── tests/                             # Comprehensive test suite (43 tests)
    ├── test_data_validation.py
    ├── test_flood_inference.py
    ├── test_road_network_criticality.py
    ├── test_accessibility.py
    ├── test_prioritization.py
    └── test_api_integration.py
```

---

## 3. Quickstart & Installation

### Prerequisites
- Python 3.11 or 3.12 (64-bit recommended)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/TanviGawade13/urban-floos-.git
cd urban-floos-

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API Server
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 4. Key API Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/api/v1/health` | Health check probe and system metadata. |
| **Diagnostics** | `GET` | `/api/v1/health/system-overview` | MLOps accuracy, graph metrics, and data validation. |
| **KPIs** | `GET` | `/api/v1/current-risk/kpis` | Real-time high-risk zone count and advisory flags. |
| **Flood Risk** | `GET` | `/api/v1/forecast-risk?horizon=NOW` | 500m grid susceptibility predictions across 1,767 sectors. |
| **Hotspots** | `GET` | `/api/v1/hotspots?limit=20` | Top vulnerable depression hotspots with elevation and SWD distance. |
| **Mobility** | `POST` | `/api/v1/safe-route` | Dynamic Dijkstra routing avoiding flood-susceptible links. |
| **Presets** | `GET` | `/api/v1/safe-route/presets` | Curated arterial transit corridor presets. |
| **Criticality** | `GET` | `/api/v1/criticality/roads` | Road segments with betweenness centrality and bridge flags. |
| **Accessibility**| `GET` | `/api/v1/accessibility/analysis` | Baseline vs disrupted travel times to trauma hospitals and fire hubs. |
| **Prioritization**| `POST` | `/api/v1/prioritization/rank` | Multi-criteria inspection ranking ($w_h, w_c, w_a, w_e$). |
| **Scenario Budget**| `POST` | `/api/v1/prioritization/compare?budget_k=5` | Strategy A (Hazard-Only) vs Strategy B (Network-Aware) comparison. |
| **Decision Report**| `GET` | `/api/v1/analytics/decision-report` | Comprehensive executive report for disaster incident commanders. |

---

## 5. Running Tests

Run the test suite:
```bash
pytest tests -v
```
All 32 deterministic unit and integration tests execute in < 7 seconds.