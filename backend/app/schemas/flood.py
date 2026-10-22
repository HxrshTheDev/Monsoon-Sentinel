"""
Flood Zone, Risk and Municipal KPI Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class FloodZoneSchema(BaseModel):
    gridId: str = Field(..., description="Unique 500m grid sector ID (e.g. CHN_G0001)")
    name: str = Field(..., description="Nearby locality or landmark identifier")
    latitude: float
    longitude: float
    bounds: List[List[float]] = Field(..., description="Bounding box [[minLat, minLon], [maxLat, maxLon]]")
    riskLevel: str = Field(..., description="NONE | LOW | MEDIUM | HIGH | CRITICAL")
    riskScore: int = Field(..., description="Integer risk score 0 to 100")
    predictionTime: str = Field(default="NOW", description="Horizon indicator (NOW, +30M, +1H, +2H, +3H)")
    rainfall: float = Field(..., description="Rainfall depth in mm")
    elevation: float = Field(..., description="Elevation above mean sea level in meters")
    waterDepth: Optional[float] = Field(None, description="Water depth in meters; explicitly null if unmeasured")
    runoffCoefficient: float = Field(default=0.75, description="Surface runoff coefficient")
    slope: str = Field(default="Flat (<2 deg)", description="Slope category")
    summary: str = Field(..., description="Plain-language vulnerability summary")
    historicalFlooding: str = Field(..., description="Historical inundation tier")
    drainageStatus: str = Field(..., description="Proximity classification to SWD drains")
    builtUpDensity: int = Field(..., description="Percentage built-up impervious surface (0-100)")
    isSimulated: bool = Field(default=False, description="Whether record is based on simulation")
    probability: Optional[float] = Field(None, description="Model-predicted flood susceptibility [0.0, 1.0]")
    provenanceStatus: ProvenanceStatus = Field(default=ProvenanceStatus.MODEL_PREDICTED)


class SystemKPIsSchema(BaseModel):
    currentRainfall: float
    rainfallDelta: str
    highRiskZones: int
    highRiskDelta: str
    unsafeRoads: int
    unsafeRoadsStatus: str
    activeAlerts: int
    highPriorityAlerts: int
    lastUpdated: str
    isSimulated: bool = False


class RecentPredictionSchema(BaseModel):
    location: str
    currentRisk: str
    plus1HourRisk: str
    plus3HoursRisk: str
    confidence: int
    isSimulated: bool = False


class RoadSegmentSchema(BaseModel):
    id: str
    name: str
    status: str = Field(..., description="SAFE | CAUTION | UNSAFE | BLOCKED")
    riskScore: int
    waterDepthCm: int
    coordinates: List[List[float]]
    avoidedBySafeRoute: bool
    locality: str

