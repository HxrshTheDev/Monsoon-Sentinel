"""
Regression tests for OSM road-following geometry, Mahim Bay non-crossing,
safer vs shortest distinction, snapping errors, and coordinate order.
"""

from __future__ import annotations

import math

import pytest

from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService


@pytest.fixture(scope="module")
def network():
    RoadNetworkService._instance = None
    svc = RoadNetworkService.get_instance()
    if not svc.network_available:
        pytest.skip("OSM road cache missing — run scripts/build_mumbai_road_network.py")
    return svc


@pytest.fixture(scope="module")
def flood():
    return FloodService.get_instance()


def _path_length_m(coords):
    total = 0.0
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        r = 6_371_000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlmb = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
        total += 2 * r * math.asin(min(1.0, math.sqrt(a)))
    return total


def _crosses_mahim_bay_chord(coords, max_water_gap_m: float = 1200.0) -> bool:
    """
    Detect a suspicious long westbound chord across Mahim Bay water.
    Real crossings (Sea Link / Causeway) are bridges with intermediate OSM nodes,
    so consecutive gaps stay modest except on tagged bridges — we flag any
    non-incremental jump that cuts through the bay bounding box.
    """
    bay = (18.995, 19.055, 72.815, 72.845)  # approx Mahim Bay water box
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        gap = _path_length_m([coords[i], coords[i + 1]])
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        in_bay = bay[0] <= mid_lat <= bay[1] and bay[2] <= mid_lon <= bay[3]
        # Straight chord across bay water: long gap whose midpoint sits in the bay box
        if in_bay and gap > max_water_gap_m:
            # Allow if both endpoints are near the causeway/sealink corridors
            return True
    return False


def test_candidates_share_endpoints(network, flood):
    res = network.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood,
    )
    rec = res["recommendedRoute"]
    assert rec["pathCoordinates"][0] == pytest.approx(res["sourceCoords"], abs=1e-4)
    assert rec["pathCoordinates"][-1] == pytest.approx(res["destCoords"], abs=1e-4)
    assert res["sourceCoords"][0] == pytest.approx(18.94, abs=0.05)
    assert res["destCoords"][0] == pytest.approx(19.09, abs=0.05)


def test_routes_follow_osm_not_single_chord(network, flood):
    res = network.calculate_safe_route(
        source="CSMT Fort",
        destination="CSMIA International Airport",
        vehicle_type="car",
        flood_service=flood,
    )
    coords = res["recommendedRoute"]["pathCoordinates"]
    assert len(coords) >= 20, "OSM road geometry should include many intermediate vertices"
    assert len(res["recommendedRoute"]["nodesVisited"]) >= 5
    chord = _path_length_m([coords[0], coords[-1]])
    assert _path_length_m(coords) >= chord * 0.95
    assert res["geometrySource"] == "openstreetmap_road_network"


def test_dadar_bandra_does_not_chord_across_mahim_bay(network, flood):
    res = network.calculate_safe_route(
        source="Dadar TT Circle",
        destination="Bandra Western Spine",
        vehicle_type="car",
        flood_service=flood,
    )
    coords = res["recommendedRoute"]["pathCoordinates"]
    assert len(coords) >= 10
    assert not _crosses_mahim_bay_chord(coords, max_water_gap_m=1500.0), (
        "Route appears to cut across Mahim Bay instead of following mapped roads"
    )
    # Path should be longer than a pure Dadar→Bandra geodesic (road detour / causeway)
    geodesic = _path_length_m([coords[0], coords[-1]])
    assert _path_length_m(coords) >= geodesic * 1.05


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
        assert res["recommendedRoute"]["pathCoordinates"] != alt["pathCoordinates"] or (
            res["recommendedRoute"]["nodesVisited"] != alt["nodesVisited"]
        )


def test_same_snapped_node_does_not_return_a_fabricated_route(network, flood):
    with pytest.raises(ValueError, match="same mapped road node"):
        network.calculate_safe_route(
            source="Dadar TT Circle",
            destination="Dadar",
            vehicle_type="car",
            flood_service=flood,
        )


def test_unsupported_location_is_rejected_not_mapped_to_csmt(network):
    with pytest.raises(ValueError, match="Unsupported Mumbai"):
        network.calculate_safe_route(source="Atlantis", destination="CSMT Fort")


def test_disconnected_or_off_network_coords_error(network, flood):
    with pytest.raises(ValueError, match="too far|outside"):
        network.calculate_safe_route(
            source_coords=[28.6139, 77.2090],  # Delhi
            dest_coords=[19.0896, 72.8656],
            vehicle_type="car",
            flood_service=flood,
        )


def test_edge_coordinates_are_lat_lon_order(network):
    # Sample a slice — full scan of 90k edges is slow
    for ed in network.edge_definitions[:: max(1, len(network.edge_definitions) // 200)]:
        for lat, lon in ed["coordinates"]:
            assert 18.5 <= lat <= 19.5, f"lat out of Mumbai range on {ed['edge_id']}: {lat}"
            assert 72.5 <= lon <= 73.2, f"lon out of Mumbai range on {ed['edge_id']}: {lon}"
        assert len(ed["coordinates"]) >= 2


def test_no_fabricated_straight_line_on_failure(network, flood):
    """Far-offshore point must error — never return a fake successful polyline."""
    with pytest.raises(ValueError):
        network.calculate_safe_route(
            source_coords=[19.05, 72.78],  # Arabian Sea west of Worli
            dest_coords=[19.06, 72.79],
            vehicle_type="car",
            flood_service=flood,
        )


def test_borivali_bandra_returns_mumbai_geometry(network, flood):
    res = network.calculate_safe_route(
        source="Borivali",
        destination="Bandra Western Spine",
        vehicle_type="car",
        flood_service=flood,
    )
    lats = [c[0] for c in res["recommendedRoute"]["pathCoordinates"]]
    lons = [c[1] for c in res["recommendedRoute"]["pathCoordinates"]]
    assert min(lats) >= 18.89 and max(lats) <= 19.35
    assert min(lons) >= 72.75 and max(lons) <= 73.05
    assert len(res["recommendedRoute"]["pathCoordinates"]) >= 30
