# Reference Component Audit & Integration Decision Record

**Repository Audited**: [Flood-Nowcasting (commit `bd5473b`)](https://github.com/rohanpilankar/Flood-Nowcasting/tree/main)  
**Author**: Rohan Pilankar & Contributors (SIH26085)  
**Target Repository**: `urban-floos-` (HackAMatch 1.0 — CityPulse Challenge)  
**Date of Audit**: October 2026  
**Auditor**: CityPulse Backend & ML Architecture Team  

---

## 1. Executive Summary & Audit Philosophy

Our team's concept for HackAMatch 1.0 (CityPulse) is a **flood-disruption decision-support system** focused on:
1. Grounded flood evidence and physical susceptibility indicators.
2. Road-network graph topology, bridge/cut-edge identification, and edge betweenness criticality.
3. Essential-service accessibility metrics (travel times from population clusters to hospitals, trauma centers, and emergency hubs under baseline vs disrupted conditions).
4. Transparent, explainable inspection prioritization.
5. Resource-constrained scenario analysis (budget $K$ crew/asset allocation comparing Hazard-Only vs Network-Aware prioritization).

The reference repository (`Flood-Nowcasting`) is an earlier multi-phase project originally developed for Smart India Hackathon (SIH26085) targeting Mumbai, later migrated and extended to Greater Chennai. It contains valuable preprocessing artifacts, geospatial grids, and an XGBoost susceptibility baseline. However, it also includes:
- An Angular 21 frontend (strictly excluded).
- An uncalibrated, resource-heavy Deep Neural Operator (DNO) hydrodynamic surrogate with ~100MB checkpoint weights and ~30MB synthetic storm tensors (unsuitable for lightweight production).
- A mock routing module that used hardcoded coordinate lists rather than dynamic network graph routing.
- Zero existing implementations of network criticality, essential-service accessibility degradation, or resource-budget prioritization.

Below is the component-by-component audit covering every directory and candidate file inspected.

---

## 2. Component-by-Component Audit

### Category A: Core Backend, API Gateway & Configuration

| # | Original File Path | Purpose & Functionality | Dependencies & Data | Suitability Assessment | License & Attribution | Destination Path | Verification & Test Strategy |
|---|---|---|---|---|---|---|---|
| A1 | `backend/app/main.py` | FastAPI application initialization, CORS middleware, lifespan events. | FastAPI, Uvicorn, Pydantic | **Adaptable**: Need to adapt lifespan, remove DNO initialization and mock database seeds, mount CityPulse routers. | SIH26085 / Rohan Pilankar (MIT/Open Collaboration) | `backend/app/main.py` | Verify startup, OpenAPI docs at `/docs`, health probe at `/api/v1/health`. |
| A2 | `backend/app/core/config.py` | Pydantic BaseSettings for study area bounds, JWT secrets, database URLs. | `pydantic-settings` | **Adaptable**: Already partly imported into root `config.py` by team member Omkar Musale. Reconciled and extended with decision-support variables. | SIH26085 / Omkar Musale & Rohan Pilankar | `config.py` & `backend/app/core/config.py` | Verify settings parse environment variables and default values properly. |
| A3 | `backend/app/api/api_router.py` | Central APIRouter mounting route modules. | FastAPI | **Adaptable**: Strip DNO, citizen auth, feedback routes; mount flood, routing, criticality, accessibility, and prioritization routers. | SIH26085 / Rohan Pilankar | `backend/app/api/api_router.py` | Verify all endpoints appear in `/openapi.json`. |
| A4 | `backend/app/schemas/provenance.py` | ProvenanceStatus enum (`OBSERVED`, `FORECAST`, `MODEL_PREDICTED`, `DERIVED`, `SIMULATED`, `UNAVAILABLE`) and ProvenanceRecord. | Pydantic | **Reusable**: Directly fulfills CityPulse requirement to expose data lineage and prevent silent assumptions. | SIH26085 / Rohan Pilankar | `backend/app/schemas/provenance.py` | Schema serialization and enum validation tests. |
| A5 | `backend/app/schemas/flood.py` | FloodZoneSchema, SystemKPIsSchema, RecentPredictionSchema, RoadSegmentSchema. | Pydantic | **Adaptable**: Ensure waterDepth defaults to null when unmeasured; enforce coordinate bounds. | SIH26085 / Rohan Pilankar | `backend/app/schemas/flood.py` | Pydantic roundtrip serialization tests. |
| A6 | `backend/app/schemas/route.py` | RouteRequestSchema, RoutePlanResultSchema, RouteOptionSchema, RouteHazardSchema. | Pydantic | **Adaptable**: Extend with network-graph metrics (`criticality_index`, `bridge_flag`, `delay_penalty`). | SIH26085 / Rohan Pilankar | `backend/app/schemas/route.py` | Test valid route requests with various vehicle types and coordinate inputs. |
| A7 | `backend/app/schemas/hotspot.py` | FloodHotspotItem, FloodDepthResponse. | Pydantic | **Reusable**: Enforces honesty regarding depth sensor absence. | SIH26085 / Rohan Pilankar | `backend/app/schemas/hotspot.py` | Test empty vs populated responses. |
| A8 | `backend/app/schemas/analytics.py` | Summary metrics schemas for rainfall and area risk ranks. | Pydantic | **Adaptable**: Augment with decision-support budget metrics and accessibility summary. | SIH26085 / Rohan Pilankar | `backend/app/schemas/analytics.py` | Verify schema validation. |
| A9 | `backend/app/api/routes/flood.py` | HTTP routes for `/forecast-risk`, `/kpis`, `/hotspots`, `/depth`. | FastAPI, FloodService | **Adaptable**: Standardize error handling, input bounds validation, and provenance tags. | SIH26085 / Rohan Pilankar | `backend/app/api/routes/flood.py` | Endpoint integration tests using FastAPI TestClient. |
| A10 | `backend/app/api/routes/routing.py` | Route planning endpoint (`/safe-route`, `/safe-route/presets`). | FastAPI, Routing / Network service | **Adaptable**: Replace hardcoded coordinate interpolation with genuine NetworkX graph pathfinding. | SIH26085 / Rohan Pilankar | `backend/app/api/routes/routing.py` | Test Dijkstra shortest path, risk avoidance, and disconnected origin/dest error handling. |
| A11 | `backend/app/api/routes/health.py` | Health and system overview endpoint. | FastAPI | **Adaptable**: Return XGBoost model status, graph node/edge counts, and dataset verification status. | SIH26085 / Rohan Pilankar | `backend/app/api/routes/health.py` | Assert HTTP 200 and healthy status. |

---

### Category B: Geospatial, Data & Network Infrastructure

| # | Original File Path | Purpose & Functionality | Dependencies & Data | Suitability Assessment | License & Attribution | Destination Path | Verification & Test Strategy |
|---|---|---|---|---|---|---|---|
| B1 | `Data/processed/grids/chennai_grid_500m.geojson` | 3,963 terrestrial 500m x 500m grid sectors covering Greater Chennai ($12.85^\circ-13.25^\circ\text{ N}, 80.09^\circ-80.35^\circ\text{ E}$). | GeoJSON, EPSG:4326 | **Reusable**: Verified clean geometry, no nulls, standard bounding polygon format. | OSM / ESA WorldCover / Open Data | `data/processed/grids/chennai_grid_500m.geojson` | Load via json/shapely; verify 3,963 features with valid bounds and centroid coordinates. |
| B2 | `Data/processed/features/chennai_static_spatial_features.parquet` | 3,963 rows x 26 columns containing static topography, drainage distance, and built-up ratios. | Parquet, pandas, pyarrow | **Reusable**: Zero missing values, pre-calculated low-lying depression scores and SWD proximities. | Sourced from SRTM/GLO-30, OSM SWD GIS | `data/processed/features/chennai_static_spatial_features.parquet` | Verify row count (3,963), column schema, zero NaNs, non-negative elevations. |
| B3 | `Data/processed/vectors/chennai_critical_infrastructure.parquet` | 1,505 critical facilities (845 hospitals, 534 clinics, 112 police stations, 14 fire stations) with WKB geometry. | Parquet, shapely, pyproj | **Reusable**: Genuine OpenStreetMap infrastructure points in UTM 44N. | OpenStreetMap (ODbL) | `data/processed/vectors/chennai_critical_infrastructure.parquet` | Parse WKB with shapely; project to WGS84; test bounding box and facility type counts. |
| B4 | `backend/app/services/drainage_graph_service.py` | Hydraulic network modeling of Adyar basin and SWD channels using Manning's equation. | Math, Python | **Adaptable / Reference**: Provides valuable node/reach coordinates, but too complex/uncalibrated for general disruption routing. | SIH26085 / Rohan Pilankar | Retain concepts in `road_network_service.py` | Test drainage outfall proximities. |
| B5 | `backend/app/api/routes/emergency.py` | Curated emergency facilities list and parquet loader. | pandas, Parquet | **Adaptable**: Extract curated hospital/fire/police landmarks for fast fallback and accessibility origins/destinations. | SIH26085 / Rohan Pilankar / OSM | `backend/app/services/data_loader_service.py` | Verify facility loading and geographic coordinates. |

---

### Category C: Model & Analytical Infrastructure

| # | Original File Path | Purpose & Functionality | Dependencies & Data | Suitability Assessment | License & Attribution | Destination Path | Verification & Test Strategy |
|---|---|---|---|---|---|---|---|
| C1 | `models/trained/chennai_xgboost_baseline.json` | Audited 25-feature XGBoost gradient boosted trees model trained on Chennai flood events. | `xgboost>=2.0.0` | **Reusable**: Lightweight (269 KB), deterministic inference latency (~15ms on CPU). | Trained model weights / Rohan Pilankar | `models/trained/chennai_xgboost_baseline.json` | Load with `xgb.Booster()`, inspect 25 feature names, run vectorized forward pass. |
| C2 | `backend/app/services/flood_service.py` | Vectorized ML inference on static features + dynamic rainfall, landmark mapping. | XGBoost, pandas, numpy | **Adaptable**: Remove arbitrary rainfall multiplier assumptions; add honest documentation and clean cache. | SIH26085 / Rohan Pilankar | `backend/app/services/flood_service.py` | Test inference produces probabilities $\in [0, 1]$ across all 3,963 sectors. |
| C3 | `models/urban_flood_dno/` & `dno_inference_service.py` | Hydrodynamic Deep Neural Operator (Fourier neural operator surrogate) with 100MB checkpoint. | PyTorch, CUDA, UrbanFloodCast | **Unsuitable**: Experimental research POC; uncalibrated for operational warning; oversized dependency footprint (PyTorch 2GB+). | UrbanFloodCast / Academic | Deliberately Excluded | N/A |
| C4 | `Data/raw/` heavy files (e.g. 42MB building footprints, 34MB DEM GeoTIFF) | Raw geospatial rasters and vector archives. | GDAL/Rasterio | **Unsuitable for commit**: Too large for git, already processed into compact parquet features. | USGS, ESA, Microsoft | Deliberately Excluded | Data provenance documented in `docs/data_sources.md`. |

---

### Category D: CityPulse Missing Components (To Be Implemented New)

The audit revealed that the reference project **completely lacked** the analytical core demanded by CityPulse:
1. **Road Network Graph Service (`backend/app/services/road_network_service.py`)**:
   - Must construct a genuine directed multi-graph using NetworkX representing major Chennai arterial corridors, subways, and bridges.
   - Must compute link length, free-flow travel time, betweenness centrality, degree centrality, and identify topological cut-edges (bridges).
   - Must support dynamic link closures and flood travel-delay penalties based on sector susceptibility scores.
2. **Essential-Service Accessibility Service (`backend/app/services/accessibility_service.py`)**:
   - Must compute shortest-path travel time from residential population centers to the nearest essential facilities (tertiary trauma hospitals, police headquarters, fire stations).
   - Must calculate accessibility degradation under hypothetical flood disruption scenarios (delay percentage, unreachable facilities, critically impacted origins).
3. **Transparent Inspection & Prioritization Service (`backend/app/services/prioritization_service.py`)**:
   - Multi-criteria decision ranking with explicit weights:
     $$S_{\text{rank}} = w_h \cdot \text{HazardScore} + w_c \cdot \text{BetweennessCriticality} + w_a \cdot \text{AccessibilityImpact} + w_e \cdot \text{FacilityExposure}$$
   - Must execute resource-constrained scenario comparison: evaluate **Strategy A (Hazard-Only)** versus **Strategy B (Network-Aware)** under fixed budget $K \in \{3, 5, 10\}$.
4. **Data Validation & Quality Assurance Service (`backend/app/services/data_loader_service.py`)**:
   - Schema enforcement, coordinate bounds validation ($12.85^\circ - 13.25^\circ\text{ N}$, $80.09^\circ - 80.35^\circ\text{ E}$), missing value checks, and data quality metrics.

---

## 3. Deliberately Excluded Components

| Component / File | Reason for Exclusion |
|---|---|
| `Frontend/` (entire directory) | Hackathon requirement: We build our own frontend independently; no copying of the reference UI. |
| `models/urban_flood_dno/` & `checkpoints/` (107MB) | Massive binary checkpoint; experimental surrogate; not validated for operational warning. |
| `Data/dno/` (tensors & simulations, ~45MB) | Synthetic hydrodynamic inputs/targets; unnecessary for decision-support backend. |
| `Data/raw/*.csv.gz`, `*.tif`, `*.kml` (~150MB) | Bulky raw data; preprocessed parquets and GeoJSON already provide necessary feature matrices. |
| `backend/app/db/` & `models/` (User, OTP, Citizen tables) | SQLite user accounts, passwords, and OTP verification are tangential to decision-support analytics. |
| `backend/app/services/dno_inference_service.py` | Coupled to excluded DNO weights and PyTorch. |
| `backend/app/api/routes/admin_users.py`, `auth.py`, `otp.py` | Administrative authentication endpoints not relevant to the CityPulse analytical API contract. |

---

## 4. Attribution & Licensing Declaration

- **Reference Source**: Sourced under academic and hackathon open collaboration from `https://github.com/rohanpilankar/Flood-Nowcasting`.
- **Adapted Files**: Any code adapted or ported from the reference repository carries an attribution header explicitly crediting Rohan Pilankar and the original SIH26085 project.
- **Third-Party Data**:
  - OpenStreetMap: © OpenStreetMap contributors (ODbL).
  - Copernicus GLO-30 DEM: European Space Agency / Copernicus Open Access.
  - ESA WorldCover: CC-BY 4.0.
  - IMD Telemetry: Open Government Data (OGD) Platform India.

