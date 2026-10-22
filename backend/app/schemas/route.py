"""
Route Planning & Mobility Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RouteRequestSchema(BaseModel):
    source: Optional[str] = None
    origin: Optional[str] = None
    destination: str
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
    pathCoordinates: List[List[float]]  # [[lat, lon], ...]
    nodesVisited: Optional[List[str]] = None
    notes: str
    isSimulated: bool = False


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
    hazards: List[RouteHazardSchema] = []
    isSimulated: bool = False


class PresetRouteSchema(BaseModel):
    id: str
    label: str
    source: str
    destination: str
    description: str

