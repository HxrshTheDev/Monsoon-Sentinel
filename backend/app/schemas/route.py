"""
Route Planning & Mobility Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RouteRequestSchema(BaseModel):
    source: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    source_coords: Optional[List[float]] = Field(None, description="[latitude, longitude] origin GPS coordinate")
    dest_coords: Optional[List[float]] = Field(None, description="[latitude, longitude] destination GPS coordinate")
    mode: Optional[str] = "vehicle"
    vehicle_type: Optional[str] = "car"  # 'car' | 'suv' | 'truck' | 'rescue'


class RouteOptionSchema(BaseModel):
    id: str
    name: str
    type: str  # 'RECOMMENDED_SAFE' | 'FASTER_ALTERNATIVE' | 'BASELINE'
    distanceKm: float
    etaMinutes: int
    safetyScore: int  # 0 to 100
    riskStatus: str  # 'SAFE' | 'CAUTION' | 'UNSAFE' | 'BLOCKED'
    floodPointsAvoided: int
    hazardExposure: str  # 'Low' | 'Medium' | 'High'
    riskExposureScore: float = 0.0  # length-weighted mean edge susceptibility
    highRiskEdgeCount: int = 0
    pathCoordinates: List[List[float]]  # [[lat, lon], ...] Leaflet order
    nodesVisited: Optional[List[str]] = None
    notes: str
    isSimulated: bool = False
    geometrySource: str = "arterial_graph_reconstruction"


class RouteHazardSchema(BaseModel):
    id: str
    title: str
    location: str
    coordinates: List[float]  # [lat, lon]
    severity: str  # 'CAUTION' | 'UNSAFE' | 'BLOCKED'
    waterDepthCm: int = 0
    status: str
    isSimulated: bool = False


class RoutePlanResultSchema(BaseModel):
    source: str
    destination: str
    sourceCoords: List[float]
    destCoords: List[float]
    recommendedRoute: RouteOptionSchema
    alternativeRoute: Optional[RouteOptionSchema] = None
    alternativeUnavailableReason: Optional[str] = None
    hazards: List[RouteHazardSchema] = []
    networkProvenance: Optional[str] = None
    geometrySource: Optional[str] = None
    warnings: List[str] = []
    isSimulated: bool = False


class PresetRouteSchema(BaseModel):
    id: str
    label: str
    source: str
    destination: str
    description: str
