"""
CityPulse API Router Aggregator
Mounts all modular REST routers under the /api/v1 prefix.
"""

from fastapi import APIRouter
from backend.app.api.routes import (
    health,
    flood,
    routing,
    criticality,
    accessibility,
    prioritization,
    analytics
)

api_router = APIRouter()

# 1. Health & Diagnostics
api_router.include_router(health.router)

# 2. Flood Susceptibility & Hotspots
api_router.include_router(flood.router)

# 3. Dynamic Safe Routing
api_router.include_router(routing.router)

# 4. Road Network Criticality & Topological Analysis (CityPulse)
api_router.include_router(criticality.router)

# 5. Essential-Service Accessibility & Disruption Analysis (CityPulse)
api_router.include_router(accessibility.router)

# 6. Inspection Prioritization & Resource-Constrained Scenarios (CityPulse)
api_router.include_router(prioritization.router)

# 7. Analytics & Executive Reports
api_router.include_router(analytics.router)

