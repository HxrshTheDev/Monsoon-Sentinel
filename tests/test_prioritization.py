"""
Tests for Prioritization and Resource-Constrained Scenario Simulation
"""

import pytest
from backend.app.services.prioritization_service import PrioritizationService


@pytest.fixture(scope="module")
def prioritization_service():
    return PrioritizationService.get_instance()


def test_ranking_sorting_and_weights(prioritization_service):
    rankings = prioritization_service.rank_inspection_priorities(
        w_hazard=0.35, w_criticality=0.30, w_accessibility=0.25, w_facilities=0.10
    )
    assert len(rankings) > 20

    # Ensure rank numbers are sequential 1, 2, 3...
    assert [r["rank"] for r in rankings] == list(range(1, len(rankings) + 1))

    # Ensure composite priority scores are non-increasing
    scores = [r["composite_priority_score"] for r in rankings]
    assert scores == sorted(scores, reverse=True)


def test_budget_comparison_strategy_delta(prioritization_service):
    comparison = prioritization_service.compare_budget_strategies(budget_k=5)
    assert comparison["budget_k"] == 5

    strat_a = comparison["strategy_a_hazard_only"]
    strat_b = comparison["strategy_b_network_aware"]

    assert len(strat_a["selected_edges"]) == 5
    assert len(strat_b["selected_edges"]) == 5

    # Strategy B must protect more or equal bridges than Strategy A
    assert strat_b["critical_bridges_safeguarded"] >= strat_a["critical_bridges_safeguarded"]

    # Strategy B must mitigate more or equal aggregate emergency delay
    assert (
        strat_b["aggregate_emergency_delay_mitigated_min"] >=
        strat_a["aggregate_emergency_delay_mitigated_min"]
    )

    delta = comparison["performance_delta"]
    assert delta["additional_bridges_safeguarded"] >= 0
    assert delta["additional_emergency_delay_saved_min"] >= 0.0


def test_budget_comparison_edge_cases(prioritization_service):
    # Minimum budget K=1
    comp_1 = prioritization_service.compare_budget_strategies(budget_k=1)
    assert comp_1["budget_k"] == 1
    assert len(comp_1["strategy_b_network_aware"]["selected_edges"]) == 1

    # Standard budget K=15
    comp_15 = prioritization_service.compare_budget_strategies(budget_k=15)
    assert comp_15["budget_k"] == 15
    assert len(comp_15["strategy_b_network_aware"]["selected_edges"]) == 15

    # Large budget K=25 (exceeds 15, tests dynamic edge capping)
    comp_25 = prioritization_service.compare_budget_strategies(budget_k=25)
    assert comp_25["budget_k"] == 25
    assert len(comp_25["strategy_b_network_aware"]["selected_edges"]) == 25
    assert "both strategies protect all major critical links" in comp_25["decision_recommendation"]


def test_unbalanced_weights_normalization(prioritization_service):
    # Raw weights that don't sum to 1.0 (e.g., sum = 10.0)
    rankings = prioritization_service.rank_inspection_priorities(
        w_hazard=5.0, w_criticality=3.0, w_accessibility=1.5, w_facilities=0.5
    )
    for r in rankings:
        # Crucial check: composite score MUST remain strictly within [0.0, 100.0]
        assert 0.0 <= r["composite_priority_score"] <= 100.0


