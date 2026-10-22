"""
Data Loader & Quality Assurance Service
Validates schemas, coordinate bounds, missing values, and loads geospatial assets.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import shapely
from pyproj import Transformer

from backend.app.core.config import settings

# UTM 43N to WGS84 Transformer (Mumbai UTM Zone 43N)
_TRANSFORMER_UTM_TO_WGS84 = Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)


class DataLoaderService:
    _instance: Optional["DataLoaderService"] = None

    @classmethod
    def get_instance(cls) -> "DataLoaderService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.grid_geojson_path = os.path.join(self.project_root, settings.GRID_GEOJSON_PATH.lstrip("./"))
        self.static_features_path = os.path.join(self.project_root, settings.STATIC_FEATURES_PATH.lstrip("./"))
        self.critical_infra_path = os.path.join(self.project_root, settings.CRITICAL_INFRA_PATH.lstrip("./"))

        self.grid_geometries: Dict[str, Dict[str, Any]] = {}
        self.static_features_df: pd.DataFrame = pd.DataFrame()
        self.critical_facilities: List[Dict[str, Any]] = []
        self.data_quality_report: Dict[str, Any] = {}

        self._load_and_validate_all()

    def _load_and_validate_all(self):
        self.grid_geometries = self._load_grid_geojson()
        self.static_features_df = self._load_static_features()
        self.critical_facilities = self._load_critical_infrastructure()
        self.data_quality_report = self._compute_quality_metrics()

    def _load_grid_geojson(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.grid_geojson_path):
            raise FileNotFoundError(f"Grid GeoJSON not found at: {self.grid_geojson_path}")

        with open(self.grid_geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        geoms: Dict[str, Dict[str, Any]] = {}
        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            gid = props.get("grid_id")
            if not gid:
                continue

            coords = feat.get("geometry", {}).get("coordinates", [[]])[0]
            if coords:
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
            else:
                lat = props.get("latitude", settings.DEFAULT_LAT)
                lon = props.get("longitude", settings.DEFAULT_LON)
                bounds = [[lat - 0.00225, lon - 0.00225], [lat + 0.00225, lon + 0.00225]]

            # Validate coordinate bounds
            lat = float(props.get("latitude", bounds[0][0]))
            lon = float(props.get("longitude", bounds[0][1]))
            assert settings.BOUNDS_MIN_LAT <= lat <= settings.BOUNDS_MAX_LAT, (
                f"Grid cell {gid} lat {lat} outside study area bounds ({settings.BOUNDS_MIN_LAT}-{settings.BOUNDS_MAX_LAT})"
            )
            assert settings.BOUNDS_MIN_LON <= lon <= settings.BOUNDS_MAX_LON, (
                f"Grid cell {gid} lon {lon} outside study area bounds ({settings.BOUNDS_MIN_LON}-{settings.BOUNDS_MAX_LON})"
            )

            geoms[gid] = {
                "latitude": lat,
                "longitude": lon,
                "bounds": bounds,
                "x_utm": props.get("x_utm"),
                "y_utm": props.get("y_utm")
            }
        return geoms

    def _load_static_features(self) -> pd.DataFrame:
        if not os.path.exists(self.static_features_path):
            raise FileNotFoundError(f"Static features parquet not found at: {self.static_features_path}")

        df = pd.read_parquet(self.static_features_path)

        # Assert no missing values in critical predictors
        required_cols = [
            "grid_id", "elevation_m", "slope_deg", "low_lying_score",
            "dist_to_swd_m", "built_up_ratio"
        ]
        for col in required_cols:
            assert col in df.columns, f"Required column '{col}' missing from static features"
            assert df[col].isna().sum() == 0, f"Column '{col}' contains {df[col].isna().sum()} null values"

        return df

    def _load_critical_infrastructure(self) -> List[Dict[str, Any]]:
        facilities: List[Dict[str, Any]] = []

        # 1. Curated anchor landmark facilities (guaranteed 24x7 representation in Greater Mumbai)
        curated_landmarks = [
            {
                "id": "HOSP-KEM-01",
                "name": "King Edward Memorial Hospital (KEM Hospital)",
                "facility_type": "hospital",
                "category": "Tertiary Trauma & Emergency Center",
                "lat": 19.0028, "lon": 72.8431,
                "locality": "Parel / Bhoiwada",
                "beds": 550,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "HOSP-SION-02",
                "name": "Lokmanya Tilak Municipal General Hospital (Sion Hospital)",
                "facility_type": "hospital",
                "category": "Metropolitan Disaster Trauma Center",
                "lat": 19.0378, "lon": 72.8606,
                "locality": "Sion / Dharavi",
                "beds": 480,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "HOSP-NAIR-03",
                "name": "Topiwala National Medical College & BYL Nair Hospital",
                "facility_type": "hospital",
                "category": "Tertiary Referral & Trauma Center",
                "lat": 18.9712, "lon": 72.8217,
                "locality": "Mumbai Central",
                "beds": 350,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "HOSP-LILAVATI-04",
                "name": "Lilavati Hospital & Research Centre",
                "facility_type": "hospital",
                "category": "Multi-Speciality Emergency Center",
                "lat": 19.0514, "lon": 72.8295,
                "locality": "Bandra West",
                "beds": 300,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "HOSP-KDAH-05",
                "name": "Kokilaben Dhirubhai Ambani Hospital",
                "facility_type": "hospital",
                "category": "Western Suburbs Tertiary Emergency Hub",
                "lat": 19.1312, "lon": 72.8252,
                "locality": "Andheri West",
                "beds": 350,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "FIRE-BYCULLA-01",
                "name": "Mumbai Fire Brigade Headquarters",
                "facility_type": "fire_station",
                "category": "State Disaster Command Dispatch",
                "lat": 18.9780, "lon": 72.8310,
                "locality": "Byculla / Central Command",
                "beds": 0,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "FIRE-ANDHERI-02",
                "name": "Andheri Fire & Rescue Station",
                "facility_type": "fire_station",
                "category": "Mid-Suburbs Heavy Rescue Hub",
                "lat": 19.1180, "lon": 72.8490,
                "locality": "Andheri East / WEH",
                "beds": 0,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "FIRE-KURLA-03",
                "name": "Kurla Fire & Rescue Station",
                "facility_type": "fire_station",
                "category": "Mithi Catchment Flood & Dewatering Dispatch",
                "lat": 19.0680, "lon": 72.8780,
                "locality": "Kurla / LBS Corridor",
                "beds": 0,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "POLICE-HQ-01",
                "name": "Mumbai Police Commissionerate Headquarters",
                "facility_type": "police",
                "category": "Metropolitan Command Center",
                "lat": 18.9440, "lon": 72.8340,
                "locality": "Crawford Market / Fort",
                "beds": 0,
                "status": "OPERATIONAL_24X7"
            },
            {
                "id": "POLICE-BANDRA-02",
                "name": "Bandra Police Divisional Headquarters",
                "facility_type": "police",
                "category": "Western Region Emergency Control",
                "lat": 19.0550, "lon": 72.8350,
                "locality": "Bandra West",
                "beds": 0,
                "status": "OPERATIONAL_24X7"
            }
        ]
        facilities.extend(curated_landmarks)

        # 2. Ingest parquet infrastructure if available
        if os.path.exists(self.critical_infra_path):
            try:
                df = pd.read_parquet(self.critical_infra_path)
                for idx, row in df.iterrows():
                    geom_wkb = row.get("geometry")
                    if not geom_wkb:
                        continue
                    try:
                        point = shapely.from_wkb(geom_wkb)
                        lon, lat = _TRANSFORMER_UTM_TO_WGS84.transform(point.x, point.y)
                        if not (settings.BOUNDS_MIN_LAT <= lat <= settings.BOUNDS_MAX_LAT and
                                settings.BOUNDS_MIN_LON <= lon <= settings.BOUNDS_MAX_LON):
                            continue

                        amenity = str(row.get("amenity", "other")).lower()
                        name = str(row.get("name") or row.get("name:en") or f"Facility {idx}").strip()
                        if amenity in ["hospital", "clinic", "fire_station", "police"]:
                            facilities.append({
                                "id": f"OSM-{row.get('id', idx)}",
                                "name": name,
                                "facility_type": amenity,
                                "category": str(row.get("healthcare:speciality") or amenity).capitalize(),
                                "lat": round(lat, 5),
                                "lon": round(lon, 5),
                                "locality": str(row.get("addr:suburb") or "Greater Mumbai Sector"),
                                "beds": int(row.get("building:levels", 1)) * 20 if amenity == "hospital" else 0,
                                "status": "OPERATIONAL"
                            })
                    except Exception:
                        continue
            except Exception as e:
                print(f"[WARN] Ingestion of critical_infrastructure.parquet skipped: {e}")

        return facilities

    def _compute_quality_metrics(self) -> Dict[str, Any]:
        return {
            "total_grid_cells": len(self.grid_geometries),
            "static_feature_rows": len(self.static_features_df),
            "static_feature_nulls": int(self.static_features_df.isna().sum().sum()),
            "total_critical_facilities": len(self.critical_facilities),
            "hospitals_count": sum(1 for f in self.critical_facilities if f["facility_type"] in ["hospital", "clinic"]),
            "fire_stations_count": sum(1 for f in self.critical_facilities if f["facility_type"] == "fire_station"),
            "police_stations_count": sum(1 for f in self.critical_facilities if f["facility_type"] == "police"),
            "crs_projected": "EPSG:32643 (UTM Zone 43N)",
            "crs_display": "EPSG:4326 (WGS84)",
            "validation_status": "PASSED_STRICT_SCHEMA"
        }

