"""
Essential-Service Accessibility API Router (CityPulse)
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Query
from backend.app.schemas.accessibility import AccessibilityAnalysisResponse
from backend.app.services.accessibility_service import AccessibilityService
from backend.app.services.data_loader_service import DataLoaderService

router = APIRouter(prefix="/accessibility", tags=["Essential Services & Disruption Accessibility"])


@router.get("/analysis", response_model=AccessibilityAnalysisResponse)
def evaluate_accessibility_disruption(
    scenario_threshold: float = Query(
        default=0.40,
        ge=0.10,
        le=0.90,
        description="Flood susceptibility threshold above which roads experience degradation"
    )
):
    service = AccessibilityService.get_instance()
    return service.evaluate_accessibility(scenario_threshold=scenario_threshold)


@router.get("/facilities")
@router.get("/emergency/facilities")
def get_critical_facilities(
    facility_type: str = Query(default="all", description="all | hospital | fire_station | police"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max facilities to return")
) -> List[Dict[str, Any]]:
    loader = DataLoaderService.get_instance()
    facs = loader.critical_facilities
    if facility_type.lower() != "all":
        facs = [f for f in facs if f["facility_type"] == facility_type.lower()]
    return facs[:limit]

