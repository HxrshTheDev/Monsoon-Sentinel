"""
Tests for XGBoost Flood Susceptibility Inference
"""

import pytest
from backend.app.services.flood_service import FloodService, AUDITED_PREDICTORS


@pytest.fixture(scope="module")
def flood_service():
    return FloodService.get_instance()


def test_xgboost_model_predictors(flood_service):
    model_features = flood_service.model.feature_names
    assert len(model_features) == 25, f"Expected 25 predictors, got {len(model_features)}"
    assert set(model_features) == set(AUDITED_PREDICTORS)


def test_flood_zones_forward_pass(flood_service):
    zones = flood_service.get_flood_zones("NOW")
    assert len(zones) == 3963, f"Expected 3,963 zones, got {len(zones)}"

    for z in zones[:50]:
        assert 0.0 <= z["probability"] <= 1.0, f"Invalid prob {z['probability']}"
        assert 0 <= z["riskScore"] <= 100
        assert z["riskLevel"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        # Crucial check: water depth must be null (not fabricated)
        assert z["waterDepth"] is None


def test_kpis_structure(flood_service):
    kpis = flood_service.get_kpis()
    assert "currentRainfall" in kpis
    assert kpis["currentRainfall"] > 0
    assert "highRiskZones" in kpis
    assert "unsafeRoads" in kpis


def test_hotspots_ranking(flood_service):
    hotspots = flood_service.get_hotspots(limit=10)
    assert len(hotspots) == 10

    # Verify descending probability order
    probs = [h["probability"] for h in hotspots]
    assert probs == sorted(probs, reverse=True)


def test_honest_depth_prediction(flood_service):
    depth = flood_service.get_depth_prediction("Velachery Basin")
    assert depth["depth_cm"] is None
    assert depth["status"] == "unavailable"
    assert "not fabricated" in depth["message"]


def test_inundation_eta_prediction(flood_service):
    res_normal = flood_service.predict_inundation_eta(rainfall_rate_mm_h=20.0, accumulated_rainfall_mm=30.0)
    assert res_normal["status"] == "STABLE_EVACUATION"
    assert res_normal["estimated_eta_minutes"] == -1

    res_severe = flood_service.predict_inundation_eta(rainfall_rate_mm_h=60.0, accumulated_rainfall_mm=50.0)
    assert res_severe["status"] in ["IMPENDING_INUNDATION", "WATCH_ADVISORY"]
    assert res_severe["estimated_eta_minutes"] > 0

