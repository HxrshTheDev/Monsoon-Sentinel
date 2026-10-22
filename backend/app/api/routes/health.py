"""
Health & System Overview API Router
"""

import json
import os
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.data_loader_service import DataLoaderService
from backend.app.services.road_network_service import RoadNetworkService

router = APIRouter(prefix="", tags=["System Health & Diagnostics"])


def _load_model_metrics() -> dict:
    """Load evaluation metadata from trained model sidecar or provenance manifest."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    candidates = [
        os.path.join(project_root, "models", "trained", "mumbai_model_evaluation.json"),
        os.path.join(project_root, "backend", "data", "mumbai", "mumbai_provenance_manifest.json"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            metrics = data.get("mlops_metrics", data)
            if "prototypeAccuracy" in metrics:
                return {
                    "algorithm": "XGBoost prototype susceptibility (25 predictors)",
                    "prototypeAccuracy": metrics.get("prototypeAccuracy"),
                    "f1Score": metrics.get("f1Score"),
                    "rocAuc": metrics.get("rocAuc"),
                    "labelSource": metrics.get("labelSource", "BMC_chronic_waterlogging_hotspot_proximity_750m"),
                    "evaluationNote": metrics.get(
                        "evaluationNote",
                        "Prototype metrics vs BMC hotspot-proximity labels — not calibrated flood probability."
                    ),
                    "modelVersion": metrics.get("modelVersion", settings.MODEL_VERSION),
                }
        except Exception:
            continue
    return {
        "algorithm": "XGBoost prototype susceptibility (25 predictors)",
        "prototypeAccuracy": None,
        "f1Score": None,
        "rocAuc": None,
        "labelSource": "BMC_chronic_waterlogging_hotspot_proximity_750m",
        "evaluationNote": "Evaluation metadata unavailable; retrain via scripts/retrain_mumbai_model.py",
        "modelVersion": settings.MODEL_VERSION,
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "challenge": "HackAMatch 1.0 (CityPulse)",
        "study_area": settings.STUDY_AREA,
        "model_version": settings.MODEL_VERSION,
        "mode": settings.DATA_MODE
    }


@router.get("/health/system-overview")
def system_overview():
    loader = DataLoaderService.get_instance()
    road_svc = RoadNetworkService.get_instance()
    metrics = _load_model_metrics()
    metrics["totalTrainedSectors"] = len(loader.grid_geometries)

    return {
        "status": "OPERATIONAL",
        "modelMetrics": metrics,
        "geospatialData": loader.data_quality_report,
        "roadNetwork": {
            "nodesCount": len(road_svc.nodes),
            "edgesCount": len(road_svc.edge_definitions),
            "criticalBridgesCount": len(road_svc.bridges_set),
            "coverageNote": "Prototype arterial graph (manually curated corridors), not a complete OSM road network."
        },
        "limitsAndCaveats": [
            "Scores are prototype flood-susceptibility estimates under scenario rainfall — not calibrated flood probabilities.",
            "Continuous hydrodynamic water depth is unmeasured and not fabricated (waterDepth: null).",
            "Road closures and routing penalties are decision-support simulations, not operational emergency advisories.",
            "Rainfall values are scenario baselines unless a live AWS feed is connected.",
            "Model metrics reflect agreement with BMC hotspot-proximity proxy labels, not chronological flood-event accuracy."
        ]
    }
