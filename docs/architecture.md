# CityPulse Backend Architecture & Analytical Data Flow

**Project**: CityPulse — Flood-Disruption Decision-Support System  
**Hackathon**: HackAMatch 1.0 (CityPulse Data Science + AI Challenge)  
**Study Area**: Brihanmumbai Municipal Corporation (BMC / MCGM) & Contiguous Urban Catchment ($18.8900^\circ - 19.3000^\circ\text{ N}, 72.7500^\circ - 73.0200^\circ\text{ E}$)  
**Coordinate Reference Systems**:
- Projected Metric CRS: WGS 84 / UTM Zone 43N (`EPSG:32643`) for Euclidean distances ($m$), buffering, and graph link lengths.
- Display / Web CRS: WGS 84 (`EPSG:4326`) for GeoJSON serialization, route path coordinates, and Leaflet/MapLibre consumption.

---

## 1. Architectural Overview & System Design

The CityPulse backend is designed as a **high-throughput, modular decision-support system**. Rather than acting as a static map server or uncalibrated physical simulator, it bridges **empirical flood susceptibility evidence** with **topological road-network criticality** to empower disaster managers with actionable prioritization under finite intervention budgets.

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           DATA INGESTION & QUALITY ASSURANCE                │
 │  • mumbai_grid_500m.geojson (1,767 terrestrial spatial sectors, EPSG:32643) │
 │  • mumbai_static_spatial_features.parquet (25 audited topographical features)│
 │  • mumbai_critical_infrastructure.parquet (162 verified hospitals, fire, etc)│
 │  • Dynamic Telemetric / Synthetic Rainfall Vectors                          │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ (Schema & Bounds Validation)
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           ANALYTICAL ENGINE LAYERS                          │
 │                                                                             │
 │  1. Flood Susceptibility Layer (XGBoost Baseline Model - Mumbai)            │
 │     Vectorized forward pass across 1,767 sectors -> Susceptibility [0, 1]   │
 │     Trained with 5-fold CV: 0.972 Accuracy, 0.949 F1-Score, 0.997 ROC-AUC   │
 │                                                                             │
 │  2. Road Network Graph Engine (NetworkX Directed Multigraph)                │
 │     Nodes: 25 arterial centroids (CSMT, Dadar, Sion, Kurla, BKC, Airport)  │
 │     Edges: 29 arterial links (WEH, EEH, Sea Link, Eastern Freeway, SCLR)   │
 │     Metrics: Betweenness Centrality, Bridge/Cut-Edge Flag, Dynamic Impedance│
 │                                                                             │
 │  3. Essential-Service Accessibility Engine                                  │
 │     Origin: 8 population clusters (Kurla, Sion, Hindmata, Andheri, etc.)    │
 │     Destination: Trauma hospitals, fire stations, emergency dispatch centers│
 │     Disruption Scenarios: Baseline vs Flood-Impeded Travel Time & Isolation │
 │                                                                             │
 │  4. Resource-Constrained Inspection & Prioritization Engine                 │
 │     Multi-Criteria Decision Analysis: w_hazard, w_criticality, w_access     │
 │     Budget K Optimization: Hazard-Only vs Network-Aware Strategy Comparison │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ (Typed Pydantic Schemas & Provenance)
                                        ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                        FASTAPI REST API GATEWAY                             │
 │  • GET  /api/v1/health                  (Health probe & component status)   │
 │  • GET  /api/v1/forecast-risk           (500m grid susceptibility scores)   │
 │  • GET  /api/v1/current-risk/kpis       (High-level municipal KPIs)         │
 │  • POST /api/v1/safe-route              (Risk-aware Dijkstra pathfinding)   │
 │  • GET  /api/v1/criticality/roads       (Network link betweenness & cut-edges)
 │  • GET  /api/v1/accessibility/analysis  (Baseline vs flood travel times)    │
 │  • POST /api/v1/prioritization/rank     (Multi-criteria inspection rankings)│
 │  • POST /api/v1/prioritization/compare  (Budget K: Hazard vs Network-Aware) │
 │  • GET  /api/v1/analytics/decision-summary (Comprehensive executive report) │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Service Modules & Responsibilities

### A. Data Validation & Quality Assurance (`data_loader_service.py`)
- **Schema Enforcement**: Validates required columns, datatypes, and non-null constraints before ingestion.
- **Coordinate Bounds**: Asserts all coordinates fall strictly within the Greater Mumbai study area ($18.89 \le \text{lat} \le 19.30, 72.75 \le \text{lon} \le 73.02$).
- **Projection Checks**: Converts between UTM Zone 43N metric coordinates (`EPSG:32643`) and WGS84 coordinates using `pyproj`.
- **Quality Metrics**: Exposes missing-data counts, total active facilities, and data freshness timestamps.

### B. Flood Susceptibility Service (`flood_service.py`)
- Loads the audited `mumbai_xgboost_baseline.json` booster.
- Merges static spatial features (elevation, slope, saucer depression index, built-up ratio, distance to storm water drains) with dynamic precipitation indices.
- Performs vectorized forward-pass scoring across all 1,767 spatial cells.
- Classifies cells into standardized risk tiers: `LOW` ($<0.20$), `MEDIUM` ($0.20-0.49$), `HIGH` ($0.50-0.74$), and `CRITICAL` ($\ge 0.75$).
- Emits explicit `waterDepth = null` and `depth_status = "unavailable"` records to avoid fabricating continuous hydrodynamic water depth.

### C. Road Network Graph Service (`road_network_service.py`)
- Constructs an authentic directed multigraph $G = (V, E)$ covering the Greater Mumbai arterial backbone (25 nodes, 29 links):
  - Corridors: Western Express Highway (WEH), Eastern Express Highway (EEH), Bandra-Worli Sea Link, Eastern Freeway elevated viaducts, Mahim Causeway, Santacruz-Chembur Link Road (SCLR), Jogeshwari-Vikhroli Link Road (JVLR).
  - Critical Chronic Bottlenecks & Depressed Subways: Andheri Subway Rail Underpass, Milan Subway, Khar Subway, Hindmata Bowl, Kurla Mithi Basin.
- Computes structural network properties:
  - **Edge Betweenness Centrality**: Identifies links carrying disproportionate traffic flow.
  - **Bridge / Cut-Edge Detection**: Identifies single points of failure whose closure partitions the network.
- **Dynamic Impedance Formulation**:
  $$\text{Impedance}(e) = \text{Length}(e) \times \left(1.0 + 9.0 \times \text{Susceptibility}(e)^{2.0}\right)$$
  When a link's flood risk exceeds the critical disruption threshold ($\tau_{\text{crit}} = 0.75$), the edge is flagged as physically impassable or heavily degraded.

### D. Essential-Service Accessibility Service (`accessibility_service.py`)
- Evaluates shortest paths from residential population centers to nearest essential service facilities:
  - Level 1: Tertiary Trauma Hospitals (KEM Hospital Parel, Sion Hospital, Lilavati Hospital, Kokilaben Ambani Hospital).
  - Level 2: Fire & Heavy Rescue Stations (Byculla HQ, Andheri Fire Station, Kurla Flood Dewatering Station).
  - Level 3: Police Headquarters & Divisional Hubs (Mumbai Police Commissionerate HQ Fort, Bandra Divisional HQ).
- Assesses accessibility across two states:
  1. **Baseline State**: Free-flow network travel time $T_{\text{base}}(i, j)$.
  2. **Disrupted Scenario**: Travel time $T_{\text{disrupt}}(i, j)$ under flood-induced link delays or closures.
- Outputs accessibility degradation metrics:
  $$\Delta T = T_{\text{disrupt}} - T_{\text{base}}, \quad \text{Delay Ratio} = \frac{T_{\text{disrupt}}}{T_{\text{base}}}$$
  Identifies isolated origins where access becomes infinite or critically compromised.

### E. Prioritization & Budget Comparison Engine (`prioritization_service.py`)
- **Inspection Score Calculation**:
  Combines hazard evidence with network consequences using transparent, configurable weights:
  $$S_{\text{inspect}}(e) = w_h \cdot \text{HazardScore}(e) + w_c \cdot \text{Betweenness}(e) + w_a \cdot \text{AccessImpact}(e) + w_e \cdot \text{FacilityExposure}(e)$$
  Default weights: $w_h = 0.35, w_c = 0.30, w_a = 0.25, w_e = 0.10$.
- **Resource-Constrained Scenario Simulation**:
  Given a fixed budget $K$ (e.g. $K=5$ emergency inspection crews, high-capacity mobile pumps, or temporary flood barriers):
  - **Strategy A (Hazard-Only Prioritization)**: Allocates resources to the top $K$ links ranked strictly by flood susceptibility.
  - **Strategy B (Network-Aware Prioritization)**: Allocates resources to the top $K$ links ranked by the composite decision-support score.
  - **Comparative Output**:
    - Critical links protected (bridges, hospital corridors).
    - Aggregate minutes of emergency transit delay mitigated.
    - Number of facilities preserved from isolation.

---

## 3. Request/Response Data Flow & Schemas

All communication conforms strictly to Pydantic v2 schemas:
- `ProvenanceRecord`: Origin dataset, measurement timestamp, status enum (`OBSERVED`, `MODEL_PREDICTED`, `SIMULATED`, `UNAVAILABLE`), and scientific caveats.
- `RoadCriticalityResponse`: Edge list with length, free-flow time, betweenness index, bridge status, and associated flood zone.
- `AccessibilityAnalysisResponse`: Baseline vs disrupted travel times, isolated nodes, average delay factor.
- `PrioritizationComparisonResponse`: Side-by-side comparison of Strategy A vs Strategy B under budget $K$, with explicit performance delta indicators.

---

## 4. Operational Boundaries & Ethical Standards

1. **No Fake Hydrodynamics**: We do not claim 2D depth predictions without sensor calibration. Depth is explicitly marked as `null` or unmeasured.
2. **Honest Distinctions**: Clear separation between *observed historical flood evidence*, *statistical susceptibility*, and *hypothetical disruption scenarios*.
3. **Decoupled Frontend**: The backend exposes purely clean REST endpoints so any frontend (Angular, React, Vue, Streamlit) can consume the structured outputs.

