# Data Sources, Provenance & Integrity Specification

**Project**: CityPulse / Monsoon Sentinel  
**Hackathon**: HackAMatch 1.0 (CityPulse Challenge)  
**Study Area**: Brihanmumbai Municipal Corporation (BMC / MCGM) & Greater Mumbai  
**Bounds**: $18.89^\circ - 19.30^\circ\text{ N}, 72.75^\circ - 73.02^\circ\text{ E}$  
**Projected Metric CRS**: `EPSG:32643` (WGS 84 / UTM Zone 43N)  
**Display / Web CRS**: `EPSG:4326` (WGS 84 Geographic)  

---

## 1. Active Datasets

| Asset | Path | Notes |
|---|---|---|
| 500m terrestrial grid | `data/processed/grids/mumbai_grid_500m.geojson` | ~1,767 land cells; GeoJSON lon/lat order |
| Static spatial features | `data/processed/features/mumbai_static_spatial_features.parquet` | 25 audited predictors; zero nulls on required columns |
| Critical infrastructure | `data/processed/vectors/mumbai_critical_infrastructure.parquet` | Hospitals, clinics, fire, police (OpenCity / OSM) |
| XGBoost model | `models/trained/mumbai_xgboost_baseline.json` | Prototype susceptibility booster |
| Evaluation metadata | `models/trained/mumbai_model_evaluation.json` | Label source + CV metrics |
| Provenance manifest | `backend/data/mumbai/mumbai_provenance_manifest.json` | CRS, counts, sources |

Raw downloads (when present) live under `backend/data/mumbai/raw/` (DEM cache, microwatersheds, rainfall CSV, hospital lists).

---

## 2. Model labels & honesty

- **ML target**: binary proximity to BMC chronic waterlogging hotspot coordinates (750 m radius in EPSG:32643).
- **Not used as ML target**: the transparent rule-based susceptibility index (elevation, low-lying score, built-up, drainage distance).
- **Metrics** (accuracy / F1 / ROC-AUC) measure agreement with the hotspot-proximity proxy under stratified CV. They are **not** calibrated real-world flood-event predictive accuracy.
- Chronological independent flood-event labels were **not** available for this prototype.
- **Water depth** is always `null` / unmeasured — never fabricated.

---

## 3. Feature notes

| Feature family | Status |
|---|---|
| Elevation / DEM-derived | From cached Copernicus-style DEM elevations where available |
| Drainage distances | Metric distances in EPSG:32643 to rivers / SWD proxies |
| `dist_to_buckingham_canal_m` | Schema-compat name mapped to **Mithi / Mahim Creek corridor** distance |
| Rainfall predictors at inference | Scenario baselines (e.g. 45 mm), not live AWS unless a feed is connected |
| Built-up / vegetation / soil | Pipeline estimates; treat as prototype predictors |

---

## 4. Road network

**Source:** OpenStreetMap highway ways via the Overpass API (ODbL).  
**Builder:** `python scripts/build_mumbai_road_network.py`  
**Cache:** `data/processed/roads/mumbai_drive_network.json.gz` (+ `.meta.json`)  
**Coverage:** Greater Mumbai bbox (`18.89–19.30 N`, `72.75–73.02 E`), arterial/collector classes by default (`motorway`…`tertiary` + link roads). Use `--full` to include residential/unclassified (larger download).  
**Geometry:** Consecutive OSM node pairs only — no synthetic chords across Mahim Bay or other water. Bridges/tunnels follow OSM tags.  
**Routing CRS:** lengths via haversine / edge `length_m`; map output `[lat, lon]` for Leaflet. Stored cache geometry is GeoJSON `[lon, lat]`.  
**Flood-aware cost:** `edge_cost = length_m + length_m * RISK_PENALTY_FACTOR * risk^RISK_PENALTY_EXPONENT` (see `config.py`). Unknown risk uses `UNKNOWN_RISK_DEFAULT` (not treated as safe).  
**Risk source:** Risk values are sampled along mapped edge geometry from the current XGBoost scenario susceptibility grid; they are not live water-depth or road-closure observations.  
Route samples are at most 250 m apart and use the nearest grid centroid within 0.008 degrees; uncovered samples make that edge unknown and apply the configured conservative default.
**Limitations:** Not live traffic; residential streets omitted unless `--full`; Overpass mirrors can fail — rebuild when the cache is missing.

---

## 5. Regeneration

```bash
# Full GIS + model rebuild (downloads / uses cached raw where possible)
python scripts/build_mumbai_pipeline.py

# Retrain model only from existing Mumbai features parquet
python scripts/retrain_mumbai_model.py
```

See also `docs/mumbai_data_sources.md` for detailed source URLs and mapping notes.
