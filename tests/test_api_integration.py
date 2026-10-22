"""
End-to-End FastAPI Integration Tests
Tests all HTTP endpoints, request validations, and response schemas.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "Brihanmumbai" in data["study_area"] or "Mumbai" in data["study_area"]
    assert data["status"] == "ONLINE"


def test_health_endpoints():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_diag = client.get("/api/v1/health/system-overview")
    assert res_diag.status_code == 200
    data = res_diag.json()
    assert data["status"] == "OPERATIONAL"
    assert data["geospatialData"]["total_grid_cells"] == 1767


def test_kpis_endpoint():
    res = client.get("/api/v1/current-risk/kpis")
    assert res.status_code == 200
    data = res.json()
    assert "currentRainfall" in data
    assert "unsafeRoads" in data
    assert data["isSimulated"] is True


def test_forecast_risk_endpoint():
    res = client.get("/api/v1/forecast-risk?horizon=NOW")
    assert res.status_code == 200
    zones = res.json()
    assert len(zones) == 1767
    assert zones[0]["waterDepth"] is None


def test_hotspots_and_depth_endpoints():
    res_hot = client.get("/api/v1/hotspots?limit=5")
    assert res_hot.status_code == 200
    hotspots = res_hot.json()
    assert len(hotspots) == 5

    res_depth = client.get("/api/v1/depth?location=Kurla%20Mithi%20River%20Basin")
    assert res_depth.status_code == 200
    depth = res_depth.json()
    assert depth["depth_cm"] is None
    assert depth["status"] == "unavailable"


def test_safe_route_endpoint():
    payload = {
        "source": "CSMT Fort",
        "destination": "CSMIA International Airport",
        "vehicle_type": "car"
    }
    res = client.post("/api/v1/safe-route", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommendedRoute" in data
    assert data["recommendedRoute"]["safetyScore"] >= 50
    assert len(data["recommendedRoute"]["pathCoordinates"]) >= 2


def test_preset_routes_endpoint():
    res = client.get("/api/v1/safe-route/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 3


def test_criticality_endpoints():
    res_roads = client.get("/api/v1/criticality/roads")
    assert res_roads.status_code == 200
    roads = res_roads.json()
    assert len(roads) >= 20

    res_overview = client.get("/api/v1/criticality/network-overview")
    assert res_overview.status_code == 200
    overview = res_overview.json()
    assert overview["overview"]["total_edges"] >= 20
    assert overview["overview"]["critical_bridges_count"] >= 1


def test_accessibility_endpoints():
    res_access = client.get("/api/v1/accessibility/analysis?scenario_threshold=0.40")
    assert res_access.status_code == 200
    data = res_access.json()
    assert data["total_origins_evaluated"] >= 5
    assert len(data["results"]) >= 5

    res_facs = client.get("/api/v1/accessibility/facilities?facility_type=hospital")
    assert res_facs.status_code == 200
    assert len(res_facs.json()) > 0


def test_prioritization_endpoints():
    # Rank endpoint
    res_rank = client.post("/api/v1/prioritization/rank", json={
        "w_hazard": 0.35, "w_criticality": 0.30, "w_accessibility": 0.25, "w_facilities": 0.10
    })
    assert res_rank.status_code == 200
    data = res_rank.json()
    assert data["total_candidates"] >= 20
    assert len(data["rankings"]) >= 20

    # Compare endpoint
    res_comp = client.post("/api/v1/prioritization/compare?budget_k=5")
    assert res_comp.status_code == 200
    comp = res_comp.json()
    assert comp["budget_k"] == 5
    assert "strategy_a_hazard_only" in comp
    assert "strategy_b_network_aware" in comp
    assert comp["performance_delta"]["additional_bridges_safeguarded"] >= 0


def test_analytics_endpoints():
    res_summary = client.get("/api/v1/analytics/summary")
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert len(data["areaRankings"]) > 0
    assert len(data["rainfallTrends"]) > 0

    res_report = client.get("/api/v1/analytics/decision-report")
    assert res_report.status_code == 200
    report = res_report.json()
    assert "budget_comparison" in report
    assert len(report["limitations_and_assumptions"]) >= 2

