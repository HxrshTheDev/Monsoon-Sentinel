"""
Safe Mobility & Routing API Router
"""

from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.route import RouteRequestSchema, RoutePlanResultSchema, PresetRouteSchema
from backend.app.services.road_network_service import RoadNetworkService
from backend.app.services.flood_service import FloodService

router = APIRouter(prefix="", tags=["Safe Mobility & Routing"])


@router.get("/safe-route/presets", response_model=List[PresetRouteSchema])
def get_preset_routes():
    service = RoadNetworkService.get_instance()
    return service.get_preset_routes()


@router.post("/safe-route", response_model=RoutePlanResultSchema)
def calculate_safe_route(payload: RouteRequestSchema):
    road_svc = RoadNetworkService.get_instance()
    flood_svc = FloodService.get_instance()
    src = payload.source or payload.origin
    if not src and not payload.source_coords:
        raise HTTPException(status_code=400, detail="Provide source/origin name or source_coords.")
    if not payload.destination and not payload.dest_coords:
        raise HTTPException(status_code=400, detail="Provide destination name or dest_coords.")
    try:
        return road_svc.calculate_safe_route(
            source=src,
            destination=payload.destination,
            vehicle_type=payload.vehicle_type or "car",
            flood_service=flood_svc,
            source_coords=payload.source_coords,
            dest_coords=payload.dest_coords,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
