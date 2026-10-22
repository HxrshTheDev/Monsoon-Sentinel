# Mumbai GIS Data Sources & Provenance

**Project**: CityPulse / Monsoon Sentinel  
**Target City**: Municipal Corporation of Greater Mumbai (MCGM / BMC), Maharashtra, India  
**Bounding Box**: $18.8900^\circ\text{ N} - 19.3000^\circ\text{ N}, 72.7500^\circ\text{ E} - 73.0200^\circ\text{ E}$  
**Centroid**: $19.0760^\circ\text{ N}$, $72.8777^\circ\text{ E}$  
**Projected Metric CRS**: `EPSG:32643` (UTM Zone 43N)  
**Display CRS**: `EPSG:4326`

---

## Active datasets

| ID | Dataset | Path / source | Notes |
|---|---|---|---|
| DS-01 | 500m grid | `data/processed/grids/mumbai_grid_500m.geojson` | ~1,767 terrestrial cells |
| DS-02 | Static features | `data/processed/features/mumbai_static_spatial_features.parquet` | 25 predictors |
| DS-03 | DEM elevations | `backend/data/mumbai/raw/mumbai_dem_elevations.json` | Cached DEM samples |
| DS-04 | Microwatersheds | `backend/data/mumbai/raw/mumbai_microwatersheds.geojson` | OpenCity / MRSAC |
| DS-05 | Emergency facilities | `data/processed/vectors/mumbai_critical_infrastructure.parquet` | OpenCity + OSM |
| DS-06 | Chronic waterlogging labels | BMC hotspot coordinates in `scripts/build_mumbai_pipeline.py` | ML training labels (750 m proximity) |
| DS-07 | Arterial road graph | `backend/app/services/road_network_service.py` | Prototype curated corridors |
| DS-08 | Rainfall scenarios | Inference horizons in `flood_service.py` | Scenario baselines — not live AWS by default |
| DS-09 | XGBoost model | `models/trained/mumbai_xgboost_baseline.json` | Prototype susceptibility |

Schema legacy: `dist_to_buckingham_canal_m` stores **Mithi / Mahim Creek** corridor distance for Mumbai.

---

## Official portals consulted

- BMC Disaster Management: https://dm.mcgm.gov.in
- OpenCity Mumbai: https://data.opencity.in/
- Geofabrik OSM India: https://download.geofabrik.de/asia/india.html
- Copernicus DEM / WorldCover open access

---

## Scientific guardrails

1. Water depth is unmeasured (`null`) — never fabricated.
2. Model metrics describe agreement with BMC hotspot-proximity labels, not calibrated flood probability.
3. Road routing is a prototype arterial graph, not a complete network or live traffic feed.
4. Rainfall telemetry endpoints are labelled scenario/demo unless a live feed is wired.
