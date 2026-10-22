"""
Flood Susceptibility & Hotspot API Router
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.flood import FloodZoneSchema, SystemKPIsSchema, RecentPredictionSchema
from backend.app.schemas.hotspot import FloodHotspotItem, FloodDepthResponse
from backend.app.services.flood_service import FloodService

router = APIRouter(prefix="", tags=["Flood Nowcasting & Risk"])


@router.get("/current-risk/kpis", response_model=SystemKPIsSchema)
def get_current_kpis():
    service = FloodService.get_instance()
    return service.get_kpis()


@router.get("/forecast-risk", response_model=List[FloodZoneSchema])
def get_forecast_risk(
    horizon: str = Query(default="NOW", description="Horizon: NOW, +30M, +1H, +2H, +3H")
):
    service = FloodService.get_instance()
    return service.get_flood_zones(horizon=horizon)


@router.get("/forecast-risk/recent", response_model=List[RecentPredictionSchema])
def get_recent_predictions():
    service = FloodService.get_instance()
    return service.get_recent_predictions()


@router.get("/hotspots", response_model=List[FloodHotspotItem])
@router.get("/flood/hotspots", response_model=List[FloodHotspotItem])
def get_flood_hotspots(limit: int = Query(default=20, ge=1, le=100)):
    service = FloodService.get_instance()
    return service.get_hotspots(limit=limit)


@router.get("/depth", response_model=FloodDepthResponse)
@router.get("/flood/depth", response_model=FloodDepthResponse)
def get_flood_depth(location: str = Query(default="Velachery Basin")):
    service = FloodService.get_instance()
    return service.get_depth_prediction(location=location)


@router.get("/map-data/zones/{grid_id}", response_model=FloodZoneSchema)
def get_zone_by_id(grid_id: str):
    service = FloodService.get_instance()
    zone = service.get_zone_by_id(grid_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Grid cell '{grid_id}' not found.")
    return zone


@router.get("/location-risk", response_model=FloodZoneSchema)
def get_location_risk(location: str = Query(..., description="Landmark or locality name")):
    service = FloodService.get_instance()
    zone = service.get_location_risk(location)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Location '{location}' not found.")
    return zone


@router.get("/predict-eta")
def predict_inundation_eta(
    rainfall_rate_mm_h: float = Query(default=40.0, ge=0.0, le=300.0),
    accumulated_rainfall_mm: float = Query(default=65.0, ge=0.0, le=500.0)
):
    service = FloodService.get_instance()
    return service.predict_inundation_eta(
        rainfall_rate_mm_h=rainfall_rate_mm_h,
        accumulated_rainfall_mm=accumulated_rainfall_mm
    )

