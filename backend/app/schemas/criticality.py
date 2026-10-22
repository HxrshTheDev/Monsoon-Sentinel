"""
Road Network Criticality & Topological Schemas (CityPulse)
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class RoadCriticalityItem(BaseModel):
    edge_id: str
    source_node: str
    target_node: str
    name: str
    length_km: float
    free_flow_speed_kmh: float
    free_flow_time_min: float
    betweenness_centrality: float = Field(..., description="Normalized edge betweenness [0.0, 1.0]")
    is_bridge_or_cut_edge: bool = Field(..., description="Topological single point of failure flag")
    flood_susceptibility: float = Field(..., description="Flood susceptibility probability [0.0, 1.0]")
    criticality_score: float = Field(..., description="Composite network criticality index [0.0, 1.0]")
    coordinates: List[List[float]] = Field(..., description="Polyline coordinates [[lat, lon], ...]")
    associated_grid_id: Optional[str] = None
    locality: str
    status: str = Field(default="OPEN", description="OPEN | DEGRADED | CLOSED_SIMULATED")


class NetworkCriticalityOverview(BaseModel):
    total_nodes: int
    total_edges: int
    total_network_length_km: float
    critical_bridges_count: int
    highly_critical_links_count: int
    average_betweenness: float
    most_critical_edge: RoadCriticalityItem
    provenance_status: ProvenanceStatus = ProvenanceStatus.DERIVED


class NetworkCriticalityResponse(BaseModel):
    overview: NetworkCriticalityOverview
    roads: List[RoadCriticalityItem]
