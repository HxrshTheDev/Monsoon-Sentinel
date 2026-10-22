"""
Flood Susceptibility & Hotspot API Router
"""

from datetime import datetime, timezone
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
def get_flood_depth(location: str = Query(default="Kurla Mithi River Basin")):
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


@router.get("/rainfall/telemetry-details")
def get_rainfall_telemetry_details():
    """Scenario rainfall demo payload — not live IMD/BMC AWS telemetry."""
    return {
        "status": "SCENARIO_DEMO",
        "isSimulated": True,
        "provenanceStatus": "SIMULATED",
        "message": (
            "Station values are deterministic monsoon scenario placeholders for hackathon demo. "
            "They are not live IMD or BMC AWS observations."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "aws_stations": [
            {"id": "AWS-MUM-01", "name": "Mumbai Airport (Santacruz AWS)", "rain_rate_mm_h": 28.5, "rain_24h_mm": 78.0, "status": "SCENARIO"},
            {"id": "AWS-MUM-02", "name": "Colaba Coastal Observatory", "rain_rate_mm_h": 22.0, "rain_24h_mm": 64.5, "status": "SCENARIO"},
            {"id": "AWS-MUM-03", "name": "Dadar (Hindmata Bowl AWS)", "rain_rate_mm_h": 36.0, "rain_24h_mm": 92.0, "status": "SCENARIO"},
            {"id": "AWS-MUM-04", "name": "Kurla (Mithi River Basin AWS)", "rain_rate_mm_h": 41.5, "rain_24h_mm": 105.0, "status": "SCENARIO"},
            {"id": "AWS-MUM-05", "name": "Andheri West (Versova AWS)", "rain_rate_mm_h": 32.0, "rain_24h_mm": 84.0, "status": "SCENARIO"},
            {"id": "AWS-MUM-06", "name": "Chembur East (Trombay AWS)", "rain_rate_mm_h": 24.5, "rain_24h_mm": 70.0, "status": "SCENARIO"},
            {"id": "AWS-MUM-07", "name": "Malad West (Link Road AWS)", "rain_rate_mm_h": 26.0, "rain_24h_mm": 75.0, "status": "SCENARIO"},
            {"id": "AWS-MUM-08", "name": "Powai Lake (Vikhroli AWS)", "rain_rate_mm_h": 19.5, "rain_24h_mm": 58.0, "status": "SCENARIO"}
        ],
        "city_aggregate": {
            "ambient_temperature_c": 27.8,
            "relative_humidity_pct": 92,
            "barometric_pressure_hpa": 1004.2,
            "wind_speed_kmh": 28.5,
            "wind_direction": "WSW",
            "mean_rainfall_rate_mm_h": 29.8,
            "soil_saturation_pct": 86.4,
            "tidal_boundary_status": "Scenario high-tide window (Arabian Sea)"
        }
    }


