"""
Road Network Criticality & Topological API Router (CityPulse)
"""

from typing import List
from fastapi import APIRouter
from backend.app.schemas.criticality import RoadCriticalityItem, NetworkCriticalityResponse, NetworkCriticalityOverview
from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService

router = APIRouter(prefix="/criticality", tags=["Network Criticality & Infrastructure Analysis"])


@router.get("/roads", response_model=List[RoadCriticalityItem])
def get_critical_roads():
    road_svc = RoadNetworkService.get_instance()
    flood_svc = FloodService.get_instance()
    return road_svc.get_road_criticality_items(flood_svc)


@router.get("/network-overview", response_model=NetworkCriticalityResponse)
def get_network_overview():
    road_svc = RoadNetworkService.get_instance()
    flood_svc = FloodService.get_instance()
    roads = road_svc.get_road_criticality_items(flood_svc)

    tot_len = sum(r["length_km"] for r in roads)
    bridges = sum(1 for r in roads if r["is_bridge_or_cut_edge"])
    highly_crit = sum(1 for r in roads if r["criticality_score"] >= 0.70)
    avg_b = sum(r["betweenness_centrality"] for r in roads) / max(1, len(roads))

    overview = NetworkCriticalityOverview(
        total_nodes=len(road_svc.nodes),
        total_edges=len(road_svc.edge_definitions),
        total_network_length_km=round(tot_len, 1),
        critical_bridges_count=bridges,
        highly_critical_links_count=highly_crit,
        average_betweenness=round(avg_b, 4),
        most_critical_edge=roads[0]
    )

    return NetworkCriticalityResponse(overview=overview, roads=roads)
