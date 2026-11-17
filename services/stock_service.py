"""
Intelligent Stock Shortage Prediction and Replenishment Analysis Service.
Compares real-time inventory against ML-forecasted commodity demand.
"""
from typing import Dict, Any, List
from database.db import get_shop_inventory, get_connection
from services.prediction_service import predict_slot_comprehensive
from config.settings import OPERATIONAL_SLOTS, SLOT_HOUR_MAP

def analyze_shop_stock_shortages(shop_id: int, target_date_str: str, day_name: str, is_weekend: int, is_holiday: int) -> Dict[str, Any]:
    """
    Computes cumulative daily forecasted demand for each commodity across all operational slots,
    compares against current shop inventory, flags stockouts, and calculates replenishment requirements.
    """
    # 1. Fetch current inventory
    inv_rows = get_shop_inventory(shop_id)
    inv_map = {r["commodity_code"]: float(r["current_stock_kg"]) for r in inv_rows}
    thresh_map = {r["commodity_code"]: float(r["safety_threshold_kg"]) for r in inv_rows}

    # Fetch shop parameters
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT registered_beneficiaries, staff_count, counters_count FROM ration_shops WHERE id = ?", (shop_id,))
        shop_meta = cursor.fetchone()

    reg_ben = shop_meta["registered_beneficiaries"] if shop_meta else 850
    staff = shop_meta["staff_count"] if shop_meta else 3
    counters = shop_meta["counters_count"] if shop_meta else 2

    # 2. Accumulate demand across all operating slots for the day
    slot_predictions = []
    total_rice_demand = 0.0
    total_wheat_demand = 0.0
    total_sugar_demand = 0.0
    total_customers = 0.0

    prev_crowd_sim = 28.0
    prev_tx_sim = 24.0

    for slot in OPERATIONAL_SLOTS:
        hour = SLOT_HOUR_MAP.get(slot, 9)
        # Check active bookings for this slot
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT booked_count FROM slot_capacity WHERE shop_id = ? AND date = ? AND time_slot = ?",
                (shop_id, target_date_str, slot)
            )
            cap_row = cursor.fetchone()
            bookings = float(cap_row["booked_count"]) if cap_row else 12.0

        slot_pred = predict_slot_comprehensive(
            shop_id=shop_id,
            date_str=target_date_str,
            day_name=day_name,
            hour=hour,
            time_slot=slot,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            bookings=bookings,
            previous_crowd=prev_crowd_sim,
            previous_transactions=prev_tx_sim,
            staff_on_duty=staff,
            counters_available=counters,
            registered_beneficiaries=reg_ben,
            rice_stock_kg=inv_map.get("RICE", 500.0),
            wheat_stock_kg=inv_map.get("WHEAT", 180.0),
            sugar_stock_kg=inv_map.get("SUGAR", 90.0)
        )

        slot_predictions.append(slot_pred)
        total_customers += slot_pred["predicted_customers"]
        total_rice_demand += slot_pred["predicted_rice_demand_kg"]
        total_wheat_demand += slot_pred["predicted_wheat_demand_kg"]
        total_sugar_demand += slot_pred["predicted_sugar_demand_kg"]

        # update rolling priors
        prev_crowd_sim = slot_pred["predicted_customers"]
        prev_tx_sim = round(slot_pred["predicted_customers"] * 0.85, 1)

    # 3. Shortage and Replenishment Analysis
    commodities_analysis = []
    specs = [
        ("RICE", "Subsidized Rice", inv_map.get("RICE", 0.0), round(total_rice_demand, 1), thresh_map.get("RICE", 150.0)),
        ("WHEAT", "Fortified Wheat", inv_map.get("WHEAT", 0.0), round(total_wheat_demand, 1), thresh_map.get("WHEAT", 80.0)),
        ("SUGAR", "Subsidized Sugar", inv_map.get("SUGAR", 0.0), round(total_sugar_demand, 1), thresh_map.get("SUGAR", 40.0)),
    ]

    has_critical_shortage = False

    for code, name, current_stock, demand, safety_stock in specs:
        net_balance = round(current_stock - demand, 1)
        shortage = round(max(0.0, demand - current_stock), 1)

        # Replenishment recommended: covers shortage + restores buffer up to safety threshold
        if current_stock < demand:
            status = "CRITICAL_SHORTAGE"
            has_critical_shortage = True
            recommended_replenish = round(shortage + safety_stock, 1)
            urgency = "HIGH"
        elif net_balance < safety_stock:
            status = "LOW_STOCK_WARNING"
            recommended_replenish = round(safety_stock - net_balance + 50.0, 1)
            urgency = "MEDIUM"
        else:
            status = "ADEQUATE"
            recommended_replenish = 0.0
            urgency = "LOW"

        commodities_analysis.append({
            "code": code,
            "name": name,
            "current_stock_kg": current_stock,
            "predicted_demand_kg": demand,
            "projected_closing_stock_kg": net_balance,
            "shortage_kg": shortage,
            "safety_stock_threshold_kg": safety_stock,
            "status": status,
            "urgency": urgency,
            "recommended_replenishment_kg": recommended_replenish
        })

    return {
        "shop_id": shop_id,
        "date": target_date_str,
        "day": day_name,
        "total_predicted_customers": round(total_customers, 1),
        "has_critical_shortage": has_critical_shortage,
        "commodities": commodities_analysis,
        "slot_breakdown": slot_predictions
    }

