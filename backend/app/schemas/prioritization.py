"""
Transparent Inspection Prioritization & Resource-Constrained Scenario Schemas (CityPulse)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.provenance import ProvenanceStatus


class InspectionPriorityItem(BaseModel):
    rank: int
    edge_id: str
    name: str
    locality: str
    hazard_score: float = Field(..., description="Normalized flood susceptibility hazard [0, 100]")
    betweenness_score: float = Field(..., description="Normalized network betweenness score [0, 100]")
    accessibility_impact: float = Field(..., description="Estimated travel delay caused to emergency routes [0, 100]")
    facility_exposure: float = Field(..., description="Proximity and criticality of nearby emergency facilities [0, 100]")
    composite_priority_score: float = Field(..., description="Weighted decision-support score [0, 100]")
    is_bridge: bool
    recommended_action: str
    coordinates: List[List[float]]


class PrioritizationWeights(BaseModel):
    w_hazard: float = Field(default=0.35, description="Weight for flood susceptibility hazard")
    w_criticality: float = Field(default=0.30, description="Weight for network betweenness centrality")
    w_accessibility: float = Field(default=0.25, description="Weight for essential-service delay impact")
    w_facilities: float = Field(default=0.10, description="Weight for emergency facility exposure")


class PrioritizationRankingResponse(BaseModel):
    total_candidates: int
    weights_applied: PrioritizationWeights
    rankings: List[InspectionPriorityItem]
    methodology: str = (
        "Multi-Criteria Decision Analysis: composite_score = w_hazard * Hazard + w_crit * Betweenness "
        "+ w_access * AccessibilityImpact + w_fac * FacilityExposure"
    )
    provenance_status: ProvenanceStatus = ProvenanceStatus.DERIVED


class StrategyMetrics(BaseModel):
    strategy_name: str
    budget_k: int
    selected_edges: List[str]
    selected_edge_names: List[str]
    critical_bridges_safeguarded: int
    aggregate_emergency_delay_mitigated_min: float
    isolated_facilities_prevented: int
    average_hazard_of_interventions: float
    average_criticality_of_interventions: float


class BudgetComparisonResponse(BaseModel):
    budget_k: int
    resource_type: str = "Inspection Crews / Rapid Intervention Deployments"
    strategy_a_hazard_only: StrategyMetrics
    strategy_b_network_aware: StrategyMetrics
    performance_delta: Dict[str, Any] = Field(
        ...,
        description="Key advantages of Network-Aware decision support over Hazard-Only allocation"
    )
    decision_recommendation: str
    provenance_status: ProvenanceStatus = ProvenanceStatus.DERIVED
