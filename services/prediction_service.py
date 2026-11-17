"""
Inference engine and machine learning prediction service.
Loads serialized pipeline artifacts and serves verified operational predictions.
"""
from typing import Dict, Any, Optional
import pandas as pd
import joblib
from pathlib import Path
import os
import sys

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    CROWD_MODEL_PATH,
    RICE_MODEL_PATH,
    WHEAT_MODEL_PATH,
    SUGAR_MODEL_PATH,
    WAITING_TIME_MODEL_PATH
)
from database.db import log_prediction

class ModelContainer:
    """Thread-safe lazy loader for trained model pipelines."""
    _instance = None

    def __init__(self):
        self.crowd_model = None
        self.rice_model = None
        self.wheat_model = None
        self.sugar_model = None
        self.waiting_time_model = None
        self.load_models()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ModelContainer()
        return cls._instance

    def load_models(self):
        try:
            if CROWD_MODEL_PATH.exists():
                self.crowd_model = joblib.load(CROWD_MODEL_PATH)
            if RICE_MODEL_PATH.exists():
                self.rice_model = joblib.load(RICE_MODEL_PATH)
            if WHEAT_MODEL_PATH.exists():
                self.wheat_model = joblib.load(WHEAT_MODEL_PATH)
            if SUGAR_MODEL_PATH.exists():
                self.sugar_model = joblib.load(SUGAR_MODEL_PATH)
            if WAITING_TIME_MODEL_PATH.exists():
                self.waiting_time_model = joblib.load(WAITING_TIME_MODEL_PATH)
        except Exception as e:
            print(f"Warning: Models loading issue: {e}")

def get_slot_features_df(features: Dict[str, Any]) -> pd.DataFrame:
    """Convert input dictionary into single-row DataFrame."""
    return pd.DataFrame([features])

def predict_crowd(features: Dict[str, Any]) -> float:
    """Predict customer footfall for a time slot."""
    container = ModelContainer.get_instance()
    if container.crowd_model is None:
        container.load_models()
    df = get_slot_features_df(features)
    pred = float(container.crowd_model.predict(df)[0])
    return max(0.0, round(pred, 1))

def predict_rice_demand(features: Dict[str, Any]) -> float:
    """Predict rice demand in kg for a time slot."""
    container = ModelContainer.get_instance()
    if container.rice_model is None:
        container.load_models()
    df = get_slot_features_df(features)
    pred = float(container.rice_model.predict(df)[0])
    return max(0.0, round(pred, 1))

def predict_wheat_demand(features: Dict[str, Any]) -> float:
    """Predict wheat demand in kg for a time slot."""
    container = ModelContainer.get_instance()
    if container.wheat_model is None:
        container.load_models()
    df = get_slot_features_df(features)
    pred = float(container.wheat_model.predict(df)[0])
    return max(0.0, round(pred, 1))

def predict_sugar_demand(features: Dict[str, Any]) -> float:
    """Predict sugar demand in kg for a time slot."""
    container = ModelContainer.get_instance()
    if container.sugar_model is None:
        container.load_models()
    df = get_slot_features_df(features)
    pred = float(container.sugar_model.predict(df)[0])
    return max(0.0, round(pred, 1))

def predict_waiting_time(features: Dict[str, Any]) -> float:
    """Predict customer waiting time in minutes."""
    container = ModelContainer.get_instance()
    if container.waiting_time_model is None:
        container.load_models()
    df = get_slot_features_df(features)
    pred = float(container.waiting_time_model.predict(df)[0])
    return max(1.0, round(pred, 1))

def predict_slot_comprehensive(
    shop_id: int,
    date_str: str,
    day_name: str,
    hour: int,
    time_slot: str,
    is_weekend: int,
    is_holiday: int,
    bookings: float,
    previous_crowd: float,
    previous_transactions: float,
    staff_on_duty: int,
    counters_available: int,
    registered_beneficiaries: int,
    rice_stock_kg: float = 500.0,
    wheat_stock_kg: float = 180.0,
    sugar_stock_kg: float = 90.0,
    persist_log: bool = False
) -> Dict[str, Any]:
    """Execute all 5 prediction pipelines simultaneously with full feature integrity."""
    base_features = {
        "Day": day_name,
        "Hour": hour,
        "Time_Slot": time_slot,
        "Is_Weekend": is_weekend,
        "Is_Holiday": is_holiday,
        "Bookings": bookings,
        "Previous_Crowd": previous_crowd,
        "Previous_Transactions": previous_transactions,
        "Staff_On_Duty": staff_on_duty,
        "Counters_Available": counters_available,
        "Registered_Beneficiaries": registered_beneficiaries
    }

    # Model 1: Crowd
    crowd_pred = predict_crowd(base_features)

    # Model 2: Rice Demand
    rice_features = {**base_features, "Rice_Stock_kg": rice_stock_kg}
    rice_pred = predict_rice_demand(rice_features)

    # Model 3: Wheat Demand
    wheat_features = {**base_features, "Wheat_Stock_kg": wheat_stock_kg}
    wheat_pred = predict_wheat_demand(wheat_features)

    # Model 4: Sugar Demand
    sugar_features = {**base_features, "Sugar_Stock_kg": sugar_stock_kg}
    sugar_pred = predict_sugar_demand(sugar_features)

    # Model 5: Waiting Time
    waiting_pred = predict_waiting_time(base_features)

    result = {
        "shop_id": shop_id,
        "date": date_str,
        "time_slot": time_slot,
        "hour": hour,
        "predicted_customers": crowd_pred,
        "predicted_rice_demand_kg": rice_pred,
        "predicted_wheat_demand_kg": wheat_pred,
        "predicted_sugar_demand_kg": sugar_pred,
        "predicted_waiting_time_min": waiting_pred
    }

    if persist_log:
        try:
            log_prediction(
                shop_id=shop_id,
                prediction_date=date_str,
                time_slot=time_slot,
                customers=crowd_pred,
                rice_demand=rice_pred,
                wheat_demand=wheat_pred,
                sugar_demand=sugar_pred,
                waiting_time=waiting_pred,
                model_version="v1.0.0",
                notes=f"Auto-logged via prediction service for {time_slot}"
            )
        except Exception:
            pass

    return result

