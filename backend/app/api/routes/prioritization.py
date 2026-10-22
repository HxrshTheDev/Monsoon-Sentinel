"""
Inspection Prioritization & Resource-Constrained Scenario API Router (CityPulse)
"""

from fastapi import APIRouter, Query, Body
from backend.app.schemas.prioritization import (
    PrioritizationRankingResponse,
    PrioritizationWeights,
    BudgetComparisonResponse
)
from backend.app.services.prioritization_service import PrioritizationService

router = APIRouter(prefix="/prioritization", tags=["Decision Support & Resource Prioritization"])


@router.post("/rank", response_model=PrioritizationRankingResponse)
def rank_inspection_priorities(
    weights: PrioritizationWeights = Body(default=PrioritizationWeights())
):
    service = PrioritizationService.get_instance()
    rankings = service.rank_inspection_priorities(
        w_hazard=weights.w_hazard,
        w_criticality=weights.w_criticality,
        w_accessibility=weights.w_accessibility,
        w_facilities=weights.w_facilities
    )
    return PrioritizationRankingResponse(
        total_candidates=len(rankings),
        weights_applied=weights,
        rankings=rankings
    )


@router.post("/compare", response_model=BudgetComparisonResponse)
def compare_budget_allocation(
    budget_k: int = Query(default=5, ge=1, le=50, description="Number of inspection teams / intervention units")
):
    service = PrioritizationService.get_instance()
    return service.compare_budget_strategies(budget_k=budget_k)

