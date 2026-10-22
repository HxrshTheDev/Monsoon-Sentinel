"""
Essential-Service Accessibility Schemas (CityPulse)
Evaluates baseline vs disrupted travel times to hospitals, trauma centers, and emergency hubs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class EssentialFacilityAccessibility(BaseModel):
    facility_id: str
    name: str
    facility_type: str  # 'hospital' | 'fire_station' | 'police'
    category: Optional[str] = None
    lat: float
    lon: float
    baseline_time_min: float
    disrupted_time_min: float
    delay_min: float
    delay_ratio: float
    is_accessible: bool
    status: str = Field(..., description="NORMAL | DELAYED | SEVERELY_DELAYED | ISOLATED")


class OriginAccessibilityResult(BaseModel):
    origin_id: str
    origin_name: str
    lat: float
    lon: float
    nearest_hospital: EssentialFacilityAccessibility
    nearest_fire_station: EssentialFacilityAccessibility
    nearest_police: EssentialFacilityAccessibility
    average_delay_min: float
    is_isolated: bool = False
    disruption_level: str = Field(..., description="LOW | MODERATE | SEVERE | ISOLATED")


class AccessibilityAnalysisResponse(BaseModel):
    scenario_name: str
    disruption_description: str
    total_origins_evaluated: int
    isolated_origins_count: int
    severely_delayed_count: int
    average_network_delay_min: float
    results: List[OriginAccessibilityResult]
    provenance_status: ProvenanceStatus = ProvenanceStatus.DERIVED
    notes: str = Field(
        default="Disrupted travel times are simulated based on susceptibility impedance models. Physical closures are scenario assumptions."
    )
