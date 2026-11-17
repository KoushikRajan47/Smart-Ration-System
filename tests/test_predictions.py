"""
Automated unit tests for ML predictions and inference service.
"""
import pytest
import sys
from pathlib import Path

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.prediction_service import (
    predict_crowd,
    predict_rice_demand,
    predict_wheat_demand,
    predict_sugar_demand,
    predict_waiting_time,
    predict_slot_comprehensive
)

@pytest.fixture
def sample_operational_features():
    return {
        "Day": "Wednesday",
        "Hour": 10,
        "Time_Slot": "10-11 AM",
        "Is_Weekend": 0,
        "Is_Holiday": 0,
        "Bookings": 15.0,
        "Previous_Crowd": 32.0,
        "Previous_Transactions": 28.0,
        "Staff_On_Duty": 3,
        "Counters_Available": 2,
        "Registered_Beneficiaries": 850
    }

def test_predict_crowd(sample_operational_features):
    crowd = predict_crowd(sample_operational_features)
    assert isinstance(crowd, float)
    assert 5.0 <= crowd <= 150.0

def test_predict_commodity_demands(sample_operational_features):
    rice_feat = {**sample_operational_features, "Rice_Stock_kg": 500.0}
    rice_pred = predict_rice_demand(rice_feat)
    assert isinstance(rice_pred, float)
    assert rice_pred > 0.0

    wheat_feat = {**sample_operational_features, "Wheat_Stock_kg": 180.0}
    wheat_pred = predict_wheat_demand(wheat_feat)
    assert isinstance(wheat_pred, float)
    assert wheat_pred > 0.0

    sugar_feat = {**sample_operational_features, "Sugar_Stock_kg": 90.0}
    sugar_pred = predict_sugar_demand(sugar_feat)
    assert isinstance(sugar_pred, float)
    assert sugar_pred > 0.0

def test_predict_waiting_time(sample_operational_features):
    wait_time = predict_waiting_time(sample_operational_features)
    assert isinstance(wait_time, float)
    assert 1.0 <= wait_time <= 60.0

def test_predict_slot_comprehensive():
    res = predict_slot_comprehensive(
        shop_id=1,
        date_str="2026-11-20",
        day_name="Wednesday",
        hour=10,
        time_slot="10-11 AM",
        is_weekend=0,
        is_holiday=0,
        bookings=12.0,
        previous_crowd=28.0,
        previous_transactions=24.0,
        staff_on_duty=3,
        counters_available=2,
        registered_beneficiaries=850,
        persist_log=False
    )
    assert res["predicted_customers"] > 0
    assert res["predicted_rice_demand_kg"] > 0
    assert res["predicted_wheat_demand_kg"] > 0
    assert res["predicted_sugar_demand_kg"] > 0
    assert res["predicted_waiting_time_min"] > 0

def test_edge_case_surge():
    surge_features = {
        "Day": "Saturday",
        "Hour": 17,
        "Time_Slot": "5-6 PM",
        "Is_Weekend": 1,
        "Is_Holiday": 1,
        "Bookings": 38.0,
        "Previous_Crowd": 75.0,
        "Previous_Transactions": 55.0,
        "Staff_On_Duty": 2,
        "Counters_Available": 1,
        "Registered_Beneficiaries": 950
    }
    crowd = predict_crowd(surge_features)
    wait = predict_waiting_time(surge_features)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
    assert crowd > 40.0
    assert wait > 5.0

