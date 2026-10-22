"""
Tests for Data Validation, Schemas, and Geographic Bounds
"""

import pytest
from backend.app.core.config import settings
from backend.app.services.data_loader_service import DataLoaderService


@pytest.fixture(scope="module")
def data_loader():
    return DataLoaderService.get_instance()


def test_grid_geometries_count_and_bounds(data_loader):
    geoms = data_loader.grid_geometries
    assert len(geoms) == 3963, f"Expected 3,963 grid cells, got {len(geoms)}"

    for gid, data in list(geoms.items())[:100]:
        lat = data["latitude"]
        lon = data["longitude"]
        assert settings.BOUNDS_MIN_LAT <= lat <= settings.BOUNDS_MAX_LAT, (
            f"Cell {gid} lat {lat} out of bounds"
        )
        assert settings.BOUNDS_MIN_LON <= lon <= settings.BOUNDS_MAX_LON, (
            f"Cell {gid} lon {lon} out of bounds"
        )
        bounds = data["bounds"]
        assert len(bounds) == 2
        assert bounds[0][0] <= bounds[1][0]  # minLat <= maxLat
        assert bounds[0][1] <= bounds[1][1]  # minLon <= maxLon


def test_static_features_schema_and_zero_nulls(data_loader):
    df = data_loader.static_features_df
    assert len(df) == 3963, f"Expected 3,963 rows, got {len(df)}"

    required_predictors = [
        "elevation_m", "slope_deg", "low_lying_score",
        "built_up_ratio", "dist_to_swd_m"
    ]
    for col in required_predictors:
        assert col in df.columns, f"Missing column {col}"
        assert df[col].isna().sum() == 0, f"Nulls found in {col}"

    assert (df["elevation_m"] >= -10.0).all(), "Unrealistic negative elevation"
    assert (df["slope_deg"] >= 0.0).all(), "Negative slope found"
    assert (df["built_up_ratio"] >= 0.0).all() and (df["built_up_ratio"] <= 1.0).all()


def test_critical_facilities_categorization(data_loader):
    facs = data_loader.critical_facilities
    assert len(facs) > 50, f"Expected >50 facilities, got {len(facs)}"

    types = {f["facility_type"] for f in facs}
    assert "hospital" in types or "clinic" in types
    assert "fire_station" in types
    assert "police" in types

    for f in facs[:50]:
        assert settings.BOUNDS_MIN_LAT <= f["lat"] <= settings.BOUNDS_MAX_LAT
        assert settings.BOUNDS_MIN_LON <= f["lon"] <= settings.BOUNDS_MAX_LON


def test_data_quality_report(data_loader):
    report = data_loader.data_quality_report
    assert report["total_grid_cells"] == 3963
    assert report["static_feature_nulls"] == 0
    assert report["validation_status"] == "PASSED_STRICT_SCHEMA"
