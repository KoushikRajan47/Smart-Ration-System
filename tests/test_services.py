"""
Automated unit tests for Recommendation and Stock Services.
"""
import pytest
import sys
from pathlib import Path

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.recommendation_service import get_slot_recommendations
from services.stock_service import analyze_shop_stock_shortages
from services.communication_service import (
    send_email,
    send_booking_reminder_email,
    send_purchase_receipt_email,
    send_instant_sms
)

def test_slot_recommendation_engine():
    recs = get_slot_recommendations(
        shop_id=1,
        target_date_str="2026-11-20",
        day_name="Wednesday",
        is_weekend=0,
        is_holiday=0
    )

    assert "all_slots" in recs
    assert len(recs["all_slots"]) > 0
    assert "best_slot" in recs
    best = recs["best_slot"]
    assert best is not None
    assert best["predicted_customers"] > 0
    assert best["predicted_waiting_time_min"] > 0
    assert best["tag"] in ["Best", "Recommended", "Moderate", "Busy", "Full"]

def test_stock_shortage_analyzer():
    res = analyze_shop_stock_shortages(
        shop_id=1,
        target_date_str="2026-11-20",
        day_name="Wednesday",
        is_weekend=0,
        is_holiday=0
    )

    assert "commodities" in res
    assert len(res["commodities"]) == 3  # Rice, Wheat, Sugar
    codes = [c["code"] for c in res["commodities"]]
    assert "RICE" in codes
    assert "WHEAT" in codes
    assert "SUGAR" in codes

    for c in res["commodities"]:
        assert c["current_stock_kg"] >= 0
        assert c["predicted_demand_kg"] >= 0
        assert c["status"] in ["ADEQUATE", "LOW_STOCK_WARNING", "CRITICAL_SHORTAGE"]
        assert c["recommended_replenishment_kg"] >= 0

def test_communication_email_sandbox():
    ok, msg = send_email(
        to_email="test.citizen@example.com",
        subject="Test PDS Subject",
        html_content="<p>Test HTML body</p>"
    )
    assert ok is True
    assert "test.citizen@example.com" in msg

def test_communication_booking_reminder():
    ok, msg = send_booking_reminder_email(
        beneficiary_email="citizen@example.com",
        beneficiary_user_id=1,
        head_of_family="Ramesh Kumar",
        booking_ref="BK-20261120-TEST",
        date_str="2026-11-20",
        time_slot="10-11 AM",
        shop_name="FPS Depot Indiranagar",
        predicted_wait=14.2
    )
    assert ok is True
    assert "BK-20261120-TEST" in msg or "citizen@example.com" in msg

def test_communication_purchase_receipt():
    ok, msg = send_purchase_receipt_email(
        beneficiary_email="citizen@example.com",
        beneficiary_user_id=1,
        head_of_family="Ramesh Kumar",
        ration_card_no="RC-KA-001",
        card_type="BPL",
        tx_ref="TX-20261120-TEST",
        date_str="2026-11-20",
        shop_name="FPS Depot Indiranagar",
        rice_kg=20.0,
        wheat_kg=10.0,
        sugar_kg=2.0,
        total_amount=70.0,
        payment_mode="SUBSIDIZED_CASH"
    )
    assert ok is True

def test_communication_instant_sms():
    ok, msg = send_instant_sms(
        to_phone="9876543210",
        message="Your slot BK-TEST is confirmed for 10-11 AM.",
        user_id=1
    )
    assert ok is True
    assert "9876543210" in msg

if __name__ == "__main__":
    pytest.main(["-v", __file__])

