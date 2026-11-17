"""
Automated unit tests for trained machine learning model artifacts.
"""
import pytest
import os
import joblib
from pathlib import Path
import sys

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    CROWD_MODEL_PATH,
    RICE_MODEL_PATH,
    WHEAT_MODEL_PATH,
    SUGAR_MODEL_PATH,
    WAITING_TIME_MODEL_PATH,
    METRICS_REPORT_PATH
)
from services.prediction_service import ModelContainer

def test_model_artifacts_exist():
    assert CROWD_MODEL_PATH.exists(), f"Crowd model missing at {CROWD_MODEL_PATH}"
    assert RICE_MODEL_PATH.exists(), f"Rice model missing at {RICE_MODEL_PATH}"
    assert WHEAT_MODEL_PATH.exists(), f"Wheat model missing at {WHEAT_MODEL_PATH}"
    assert SUGAR_MODEL_PATH.exists(), f"Sugar model missing at {SUGAR_MODEL_PATH}"
    assert WAITING_TIME_MODEL_PATH.exists(), f"Waiting time model missing at {WAITING_TIME_MODEL_PATH}"

def test_model_pipelines_loadable():
    container = ModelContainer.get_instance()
    container.load_models()

    assert container.crowd_model is not None
    assert container.rice_model is not None
    assert container.wheat_model is not None
    assert container.sugar_model is not None
    assert container.waiting_time_model is not None

def test_evaluation_metrics_validity():
    import json
    assert METRICS_REPORT_PATH.exists()
    with open(METRICS_REPORT_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    for task_name in ["crowd", "rice_demand", "wheat_demand", "sugar_demand", "waiting_time"]:
        assert task_name in metrics
        res = metrics[task_name]
        assert "best_metrics" in res
        m = res["best_metrics"]
        assert m["test_r2"] > 0.50, f"R2 score for {task_name} should exceed 0.50"
        assert m["test_rmse"] > 0.0
        assert m["test_mae"] > 0.0

if __name__ == "__main__":
    pytest.main(["-v", __file__])

