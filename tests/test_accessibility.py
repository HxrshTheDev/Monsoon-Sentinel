"""
Tests for Essential-Service Accessibility and Disruption Impact
"""

import pytest
from backend.app.services.accessibility_service import AccessibilityService


@pytest.fixture(scope="module")
def accessibility_service():
    return AccessibilityService.get_instance()


def test_accessibility_evaluation_structure(accessibility_service):
    res = accessibility_service.evaluate_accessibility(scenario_threshold=0.40)
    assert res["total_origins_evaluated"] == len(accessibility_service.origins)
    assert res["average_network_delay_min"] >= 0.0
    assert len(res["results"]) == len(accessibility_service.origins)


def test_origin_accessibility_results(accessibility_service):
    res = accessibility_service.evaluate_accessibility(scenario_threshold=0.40)
    for origin in res["results"]:
        assert "nearest_hospital" in origin
        assert "nearest_fire_station" in origin
        assert "nearest_police" in origin

        hosp = origin["nearest_hospital"]
        assert hosp["baseline_time_min"] >= 0.0
        assert hosp["disrupted_time_min"] >= hosp["baseline_time_min"]
        assert hosp["delay_min"] >= 0.0
        assert hosp["is_accessible"] is True
        assert hosp["status"] in ["NORMAL", "DELAYED", "SEVERELY_DELAYED", "ISOLATED"]


def test_severe_scenario_threshold(accessibility_service):
    res_mild = accessibility_service.evaluate_accessibility(scenario_threshold=0.60)
    res_severe = accessibility_service.evaluate_accessibility(scenario_threshold=0.25)

    # A more severe threshold (disrupting more links) should produce higher or equal network delay
    assert res_severe["average_network_delay_min"] >= res_mild["average_network_delay_min"]
