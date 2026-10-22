"""
Retrain Mumbai XGBoost susceptibility model from existing processed features.
Does not regenerate GIS grids or download data.

Labels: BMC chronic waterlogging hotspot proximity (independent of the rule-based index).
"""

import json
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from scripts.build_mumbai_pipeline import train_mumbai_xgboost_model  # noqa: E402


def main():
    feat_path = os.path.join(
        PROJECT_ROOT, "data", "processed", "features", "mumbai_static_spatial_features.parquet"
    )
    model_out = os.path.join(PROJECT_ROOT, "models", "trained", "mumbai_xgboost_baseline.json")
    meta_out = os.path.join(PROJECT_ROOT, "models", "trained", "mumbai_model_evaluation.json")
    manifest_path = os.path.join(
        PROJECT_ROOT, "backend", "data", "mumbai", "mumbai_provenance_manifest.json"
    )

    if not os.path.exists(feat_path):
        raise FileNotFoundError(f"Missing features parquet: {feat_path}")

    df = pd.read_parquet(feat_path)
    print(f"[LOAD] {len(df)} Mumbai feature rows from {feat_path}")

    booster, metrics = train_mumbai_xgboost_model(df)
    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    booster.save_model(model_out)
    print(f"[SAVE] Model -> {model_out}")

    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[SAVE] Evaluation metadata -> {meta_out}")

    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["mlops_metrics"] = metrics
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"[UPDATE] Provenance manifest metrics refreshed")

    print("=== Retrain complete ===")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
