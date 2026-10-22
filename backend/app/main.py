"""
CityPulse — FastAPI Backend Application
AI-Powered Urban Flood Disruption & Decision-Support System (Greater Chennai Corporation)
HackAMatch 1.0 Challenge
"""

import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure repo root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings
from backend.app.api.api_router import api_router
from backend.app.services.data_loader_service import DataLoaderService
from backend.app.services.flood_service import FloodService
from backend.app.services.road_network_service import RoadNetworkService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize data loaders, models, and network graph
    print(f"[STARTUP] Initializing CityPulse Decision-Support Engine for {settings.STUDY_AREA}...")
    DataLoaderService.get_instance()
    FloodService.get_instance()
    RoadNetworkService.get_instance()
    print("[READY] All geospatial features, XGBoost baseline nowcaster, and NetworkX road graphs initialized.")
    yield
    print("[SHUTDOWN] CityPulse backend service stopped.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "High-resolution AI-powered urban flood susceptibility, road network criticality, "
        "essential-service accessibility, and resource-constrained scenario decision support for Greater Chennai."
    ),
    version="2.0.0-citypulse",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "challenge": "HackAMatch 1.0 (CityPulse)",
        "study_area": settings.STUDY_AREA,
        "model_version": settings.MODEL_VERSION,
        "api_v1": settings.API_V1_STR,
        "api_docs": "/docs",
        "status": "ONLINE"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

