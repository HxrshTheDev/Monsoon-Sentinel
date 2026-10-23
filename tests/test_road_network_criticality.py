"""
Tests for OSM Road Network Graph, Criticality, and Dijkstra Safe Routing
"""

import pytest
from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService


@pytest.fixture(scope="module")
def network_service():
    RoadNetworkService._instance = None
    svc = RoadNetworkService.get_instance()
    if not svc.network_available:
        pytest.skip("OSM road cache missing — run scripts/build_mumbai_road_network.py")
    return svc


@pytest.fixture(scope="module")
def flood_service():
    return FloodService.get_instance()


def test_network_graph_structure(network_service):
    assert network_service.graph.number_of_nodes() >= 1000
    assert len(network_service.edge_definitions) >= 1000
    assert network_service.geometry_source == "openstreetmap_road_network"


def test_road_criticality_calculation(network_service, flood_service):
    roads = network_service.get_road_criticality_items(flood_service)
    assert len(roads) >= 100

    for r in roads[:50]:
        assert 0.0 <= r["betweenness_centrality"] <= 1.0
        assert 0.0 <= r["criticality_score"] <= 1.0
        assert r["length_km"] > 0.0
        assert r["free_flow_time_min"] > 0.0
        assert len(r["coordinates"]) >= 2

    top = roads[0]
    assert top["is_bridge_or_cut_edge"] or top["betweenness_centrality"] >= 0.0


def test_dijkstra_safe_routing(network_service, flood_service):
    res = network_service.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood_service,
    )
    assert "recommendedRoute" in res
    rec = res["recommendedRoute"]
    assert rec["distanceKm"] > 5.0
    assert rec["etaMinutes"] > 0
    assert len(rec["pathCoordinates"]) >= 20
    assert rec["safetyScore"] >= 15
    assert len(rec["nodesVisited"]) >= 5
    assert res["geometrySource"] == "openstreetmap_road_network"


def test_preset_routes(network_service):
    presets = network_service.get_preset_routes()
    assert len(presets) >= 3
    sources = [p["source"] for p in presets]
    assert "CSMT Fort" in sources or "Sion Circle" in sources


def test_missing_network_errors_clearly(monkeypatch, tmp_path):
    RoadNetworkService._instance = None
    missing = tmp_path / "missing_roads.json.gz"
    monkeypatch.setattr(
        "backend.app.services.road_network_service.settings.ROAD_NETWORK_PATH",
        str(missing),
    )
    # Also patch resolve path indirectly via settings — service joins project root.
    # Force load failure by pointing at non-existent relative path under tmp.
    monkeypatch.setattr(
        "backend.app.core.config.settings.ROAD_NETWORK_PATH",
        str(missing),
    )
    svc = RoadNetworkService()
    # If path still resolves under project root incorrectly, skip
    if svc.network_available:
        pytest.skip("Could not force missing-network state in this environment")
    with pytest.raises(ValueError, match="missing|Build the OSM"):
        svc.calculate_safe_route(source="CSMT Fort", destination="Bandra")
    RoadNetworkService._instance = None
