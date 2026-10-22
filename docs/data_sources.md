# Data Sources, Provenance & Integrity Specification

**Project**: CityPulse — Urban Flood Disruption & Decision-Support System  
**Hackathon**: HackAMatch 1.0 (CityPulse Challenge)  
**Study Area**: Greater Chennai Corporation (GCC) & Contiguous Urban Catchment ($12.85^\circ - 13.25^\circ\text{ N}, 80.09^\circ - 80.35^\circ\text{ E}$)  
**Projected Metric CRS**: `EPSG:32644` (WGS 84 / UTM Zone 44N)  
**Display / Web CRS**: `EPSG:4326` (WGS 84 Geographic)  

---

## 1. Study Area Scope & Bounding Definition

The analytical scope covers the metropolitan area of Greater Chennai, Tamil Nadu, India:
- **Southern Boundary**: $12.85^\circ\text{ N}$ (Tambaram / Vandalur / Mudichur lowlands)
- **Northern Boundary**: $13.25^\circ\text{ N}$ (Ennore / Manali industrial corridor)
- **Western Boundary**: $80.09^\circ\text{ E}$ (Poonamallee / Ambattur catchment)
- **Eastern Boundary**: $80.35^\circ\text{ E}$ (Bay of Bengal coastline)

All metric calculations (distances in meters, road lengths in kilometers, drainage density in $\text{m/km}^2$) use **EPSG:32644**, preserving spatial proportionality without spherical distortion.

---

## 2. Ingested Datasets Inventory

### DS-01: 500m Spatial Grid Partition (`chennai_grid_500m.geojson`)
- **Source**: Sourced from ESA WorldCover and OpenStreetMap administrative boundary clips.
- **Format & Size**: GeoJSON, 1.7 MB, 3,963 terrestrial polygons.
- **Coverage**: Full metropolitan area partitioned into uniform $500\text{m} \times 500\text{m}$ cells ($0.25\text{ km}^2$ each). 1,021 deep oceanic cells in the Bay of Bengal were masked out using ESA WorldCover water classifications.
- **Licensing**: Open Database License (ODbL) / Creative Commons.
- **Quality Checks**: Verified zero coordinate nulls, valid non-intersecting polygon geometries.

### DS-02: Static Topography & Drainage Features (`chennai_static_spatial_features.parquet`)
- **Source**:
  - Topography: Copernicus GLO-30 Digital Elevation Model (30m DSM) & NASA SRTM.
  - Storm Water Drains (SWD): Greater Chennai Corporation (GCC) GIS & OpenStreetMap waterways.
  - Land Cover: ESA WorldCover 2021 10m global land use raster.
- **Format & Size**: Apache Parquet, 451 KB, 3,963 rows $\times$ 26 columns.
- **Predictors**:
  - `elevation_m`: Mean ground elevation relative to MSL ($0.5\text{m} - 98.9\text{m}$).
  - `slope_deg`: Terrain gradient angle ($0.0^\circ - 35.5^\circ$).
  - `low_lying_score`: Relative saucer depression index in a 3km moving window ($[0.0, 1.0]$).
  - `dist_to_swd_m`: Distance to nearest stormwater box drain or canal ($m$).
  - `built_up_ratio`: Proportion of impervious concrete/asphalt surface ($[0.0, 1.0]$).
  - `dist_to_buckingham_canal_m`, `dist_to_river_stream_m`: Proximity to Adyar, Cooum, and Buckingham waterways.
- **Licensing**: Copernicus Open Access (ESA) / USGS Open Data / CC-BY 4.0.
- **Integrity**: Zero missing values across all 3,963 cells; strictly positive metric distances.

### DS-03: Critical Infrastructure & Essential Services (`chennai_critical_infrastructure.parquet`)
- **Source**: OpenStreetMap (OSM) healthcare, emergency, and municipal infrastructure extracts.
- **Format & Size**: GeoParquet / Parquet with WKB geometry, 193 KB, 1,505 features.
- **Breakdown**:
  - Hospitals: 845 facilities (including tertiary trauma centers like Rajiv Gandhi Govt General Hospital, Stanley Medical, Apollo Greams, Fortis Malar).
  - Clinics: 534 local primary health centers.
  - Police Stations: 112 law enforcement stations.
  - Fire Stations: 14 primary fire and rescue stations.
- **Geometry**: Well-Known Binary (WKB) Point features in UTM Zone 44N (`EPSG:32644`), dynamically projected to WGS84 for API serialization.
- **Licensing**: Open Database License (ODbL) © OpenStreetMap contributors.

### DS-04: Road Network Backbone Graph
- **Source**: OpenStreetMap Highway Network topology verified against Chennai Comprehensive Mobility Plan (CMP).
- **Corridors Included**:
  - Primary Arteries: Anna Salai (NH 45), GST Road, OMR IT Expressway, ECR Coastal Road.
  - Ring Roads & Bypasses: Inner Ring Road (100 Feet Rd), Chennai Bypass (NH 32 / NH 48 link), Outer Ring Road.
  - Critical Subways & Underpasses: Vyasarpadi, Perambur, Villivakkam, Alandur subway links.
- **Attributes**: Length ($km$), free-flow vehicle speed ($km/h$), lane capacity, and spatial association with underlying 500m flood susceptibility cells.
- **Licensing**: ODbL © OpenStreetMap contributors.

### DS-05: Machine Learning Baseline Booster (`chennai_xgboost_baseline.json`)
- **Source**: Pretrained XGBoost v2.0 classifier trained on chronological Chennai extreme monsoon events (e.g. 2015 deluge, Michaung cyclone 2023).
- **Format & Size**: JSON booster format, 269 KB, 25 input predictors.
- **Output**: Calibrated flood susceptibility probability $P(\text{flood} \mid \mathbf{x}) \in [0.0, 1.0]$.
- **Licensing**: Open collaboration (SIH26085 / Rohan Pilankar).

---

## 3. Provenance & Scientific Guardrails

To prevent hallucinated data and maintain rigorous engineering integrity:

| Data Aspect | Implementation State | Operational Caveat |
|---|---|---|
| **Flood Susceptibility** | Model-Predicted | Sourced from 25 audited physical and meteorological features. Does not claim to replace 2D hydraulic flood propagation models. |
| **Water Depth** | Explicitly Unmeasured (`null`) | No ultrasonic depth sensors are connected to every grid cell. Continuous water depth is **NOT** fabricated. |
| **Road Disruptions** | Hypothetical Scenarios | Disrupted roads are decision-support simulations to assess network vulnerability, **NOT** confirmed physical barrier closures. |
| **Rainfall Inputs** | Dynamic / Scenario-Driven | Default baseline reflects 24-hour antecedent monsoon rainfall (45mm baseline, 65mm heavy scenario). |

---

## 4. Coordinate Reference System Conversions

- All storage of spatial feature centroids and critical infrastructure points is performed with explicit CRS tracking:
  - Coordinate pairs serialized to client applications are formatted as `[latitude, longitude]` or GeoJSON `[lon, lat]` in **WGS 84 (`EPSG:4326`)**.
  - Internal distance calculations, Euclidean nearest-neighbor lookups, and network segment lengths are evaluated in **UTM Zone 44N (`EPSG:32644`)** using `pyproj.Transformer.from_crs("EPSG:32644", "EPSG:4326", always_xy=True)`.

