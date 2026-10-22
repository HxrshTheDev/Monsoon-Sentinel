"""
Regression tests for distinct safer vs alternative arterial routes,
endpoint consistency, geometry continuity, and honest unavailable alternatives.
"""

from __future__ import annotations

import math

import pytest

from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService


@pytest.fixture(scope="module")
def network():
    # Fresh instance so densified graph from this module is used
    RoadNetworkService._instance = None
    return RoadNetworkService.get_instance()


@pytest.fixture(scope="module")
def flood():
    return FloodService.get_instance()


def _path_length_deg(coords):
    total = 0.0
    for i in range(len(coords) - 1):
        total += math.hypot(coords[i][0] - coords[i + 1][0], coords[i][1] - coords[i + 1][1])
    return total


def test_candidates_share_endpoints(network, flood):
    res = network.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood,
    )
    rec = res["recommendedRoute"]
    assert rec["pathCoordinates"][0] == pytest.approx(res["sourceCoords"], abs=1e-6)
    assert rec["pathCoordinates"][-1] == pytest.approx(res["destCoords"], abs=1e-6)
    assert res["sourceCoords"][0] == pytest.approx(18.94, abs=0.05)
    assert res["destCoords"][0] == pytest.approx(19.09, abs=0.05)

    alt = res.get("alternativeRoute")
    if alt:
        assert alt["pathCoordinates"][0] == pytest.approx(res["sourceCoords"], abs=1e-6)
        assert alt["pathCoordinates"][-1] == pytest.approx(res["destCoords"], abs=1e-6)


def test_routes_are_not_duplicated_when_alternative_exists(network, flood):
    res = network.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood,
    )
    alt = res.get("alternativeRoute")
    assert alt is not None, "CSMT→Airport must expose a distinct corridor on the arterial graph"
    rec_nodes = res["recommendedRoute"]["nodesVisited"]
    alt_nodes = alt["nodesVisited"]
    assert rec_nodes and alt_nodes
    assert rec_nodes != alt_nodes
    # Geometry must differ — not merely different IDs
    assert res["recommendedRoute"]["pathCoordinates"] != alt["pathCoordinates"]
    assert res["recommendedRoute"]["id"] != alt["id"]


def test_safer_route_has_lower_or_equal_risk(network, flood):
    res = network.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood,
    )
    safer = res["recommendedRoute"]["riskExposureScore"]
    alt = res.get("alternativeRoute")
    if alt:
        assert safer <= alt["riskExposureScore"] + 1e-6


def test_geometry_follows_graph_not_single_chord(network, flood):
    res = network.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood,
    )
    coords = res["recommendedRoute"]["pathCoordinates"]
    assert len(coords) >= 8, "densified arterial polyline expected"
    assert len(res["recommendedRoute"]["nodesVisited"]) >= 3
    # Path length should exceed ~70% of pure origin→dest chord in degree space
    chord = math.hypot(
        coords[0][0] - coords[-1][0],
        coords[0][1] - coords[-1][1],
    )
    assert _path_length_deg(coords) >= chord * 0.95


def test_intra_precinct_honest_no_fake_alternative(network, flood):
    res = network.calculate_safe_route(
        source="Dadar TT Circle",
        destination="Dadar",
        vehicle_type="car",
        flood_service=flood,
    )
    assert res["alternativeRoute"] is None
    assert res.get("alternativeUnavailableReason")
    assert res["recommendedRoute"]["pathCoordinates"]


def test_disconnected_or_off_network_coords_error(network, flood):
    with pytest.raises(ValueError, match="too far"):
        network.calculate_safe_route(
            source_coords=[28.6139, 77.2090],  # Delhi
            dest_coords=[19.0896, 72.8656],
            vehicle_type="car",
            flood_service=flood,
        )


def test_edge_coordinates_are_lat_lon_order(network):
    for ed in network.edge_definitions:
        for lat, lon in ed["coordinates"]:
            assert 18.5 <= lat <= 19.5, f"lat out of Mumbai range on {ed['edge_id']}: {lat}"
            assert 72.5 <= lon <= 73.2, f"lon out of Mumbai range on {ed['edge_id']}: {lon}"
        assert len(ed["coordinates"]) >= 4


def test_borivali_bandra_returns_mumbai_nodes(network, flood):
    res = network.calculate_safe_route(
        source="Borivali",
        destination="Bandra Western Spine",
        vehicle_type="car",
        flood_service=flood,
    )
    for nid in res["recommendedRoute"]["nodesVisited"]:
        assert nid.startswith("MUM-NODE-")
    lats = [c[0] for c in res["recommendedRoute"]["pathCoordinates"]]
    assert min(lats) >= 18.89 and max(lats) <= 19.35
