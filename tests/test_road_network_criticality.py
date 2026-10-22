"""
Tests for Road Network Graph, Criticality, and Dijkstra Safe Routing
"""

import pytest
from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService


@pytest.fixture(scope="module")
def network_service():
    return RoadNetworkService.get_instance()


@pytest.fixture(scope="module")
def flood_service():
    return FloodService.get_instance()


def test_network_graph_structure(network_service):
    assert len(network_service.nodes) >= 20
    assert len(network_service.edge_definitions) >= 25
    assert len(network_service.bridges_set) >= 1


def test_road_criticality_calculation(network_service, flood_service):
    roads = network_service.get_road_criticality_items(flood_service)
    assert len(roads) == len(network_service.edge_definitions)

    for r in roads:
        assert 0.0 <= r["betweenness_centrality"] <= 1.0
        assert 0.0 <= r["criticality_score"] <= 1.0
        assert r["length_km"] > 0.0
        assert r["free_flow_time_min"] > 0.0
        assert len(r["coordinates"]) >= 2

    # Most critical link should have high betweenness or be a bridge
    top = roads[0]
    assert top["is_bridge_or_cut_edge"] or top["betweenness_centrality"] > 0.05


def test_dijkstra_safe_routing(network_service, flood_service):
    res = network_service.calculate_safe_route(
        source="Velachery",
        destination="Chennai Central",
        vehicle_type="car",
        flood_service=flood_service
    )
    assert "recommendedRoute" in res
    rec = res["recommendedRoute"]
    assert rec["distanceKm"] > 5.0
    assert rec["etaMinutes"] > 0
    assert len(rec["pathCoordinates"]) >= 2
    assert rec["safetyScore"] >= 50
    assert len(rec["nodesVisited"]) >= 3


def test_preset_routes(network_service):
    presets = network_service.get_preset_routes()
    assert len(presets) >= 3
    sources = [p["source"] for p in presets]
    assert "Chennai Central" in sources or "Velachery" in sources
