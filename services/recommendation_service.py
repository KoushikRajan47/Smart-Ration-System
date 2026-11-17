"""
Intelligent Time-Slot Recommendation Engine.
Evaluates time slots using ML Crowd & Waiting Time predictions combined with capacity quotas.
"""
from typing import List, Dict, Any, Optional
from database.db import get_connection, get_or_create_slot_capacity
from services.prediction_service import predict_slot_comprehensive
from config.settings import OPERATIONAL_SLOTS, SLOT_HOUR_MAP

def get_slot_recommendations(
    shop_id: int,
    target_date_str: str,
    day_name: str,
    is_weekend: int,
    is_holiday: int
) -> Dict[str, Any]:
    """
    Evaluates each operational slot, runs ML predictions for crowd and waiting time,
    factors in capacity constraints, tags recommendation categories, and ranks options.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT registered_beneficiaries, staff_count, counters_count FROM ration_shops WHERE id = ?", (shop_id,))
        shop_row = cursor.fetchone()

    reg_ben = shop_row["registered_beneficiaries"] if shop_row else 850
    staff = shop_row["staff_count"] if shop_row else 3
    counters = shop_row["counters_count"] if shop_row else 2

    slot_evaluations = []
    prev_crowd_sim = 26.0
    prev_tx_sim = 22.0

    for slot in OPERATIONAL_SLOTS:
        hour = SLOT_HOUR_MAP.get(slot, 9)
        cap_row = get_or_create_slot_capacity(shop_id, target_date_str, slot)
        max_cap = cap_row["max_capacity"]
        booked = cap_row["booked_count"]
        is_open = bool(cap_row["is_open"])
        available_seats = max(0, max_cap - booked)

        # ML predictions for this slot
        preds = predict_slot_comprehensive(
            shop_id=shop_id,
            date_str=target_date_str,
            day_name=day_name,
            hour=hour,
            time_slot=slot,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            bookings=float(booked),
            previous_crowd=prev_crowd_sim,
            previous_transactions=prev_tx_sim,
            staff_on_duty=staff,
            counters_available=counters,
            registered_beneficiaries=reg_ben,
            persist_log=False
        )

        pred_crowd = preds["predicted_customers"]
        pred_wait = preds["predicted_waiting_time_min"]

        # Tag slot status
        if not is_open:
            tag = "Closed"
            tag_color = "gray"
            eligibility = False
        elif available_seats <= 0:
            tag = "Full"
            tag_color = "red"
            eligibility = False
        elif pred_wait <= 7.0 and pred_crowd <= 35:
            tag = "Best"
            tag_color = "green"
            eligibility = True
        elif pred_wait <= 11.0:
            tag = "Recommended"
            tag_color = "blue"
            eligibility = True
        elif pred_wait <= 16.0:
            tag = "Moderate"
            tag_color = "orange"
            eligibility = True
        else:
            tag = "Busy"
            tag_color = "red"
            eligibility = True

        # Composite score: lower is better (waiting time + 0.2 * crowd - capacity availability bonus)
        composite_score = pred_wait + (0.15 * pred_crowd) if eligibility else 9999.0

        slot_evaluations.append({
            "time_slot": slot,
            "hour": hour,
            "predicted_customers": pred_crowd,
            "predicted_waiting_time_min": pred_wait,
            "booked_count": booked,
            "max_capacity": max_cap,
            "available_capacity": available_seats,
            "is_open": is_open,
            "tag": tag,
            "tag_color": tag_color,
            "eligible": eligibility,
            "score": composite_score
        })

        prev_crowd_sim = pred_crowd
        prev_tx_sim = round(pred_crowd * 0.85, 1)

    # Rank eligible slots
    eligible_slots = [s for s in slot_evaluations if s["eligible"]]
    eligible_slots.sort(key=lambda x: x["score"])

    best_slot = eligible_slots[0] if eligible_slots else None
    alternative_slots = eligible_slots[1:3] if len(eligible_slots) > 1 else []

    return {
        "shop_id": shop_id,
        "date": target_date_str,
        "day": day_name,
        "all_slots": slot_evaluations,
        "best_slot": best_slot,
        "alternative_slots": alternative_slots
    }

