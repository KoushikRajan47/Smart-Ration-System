"""
Authentication and session authorization service.
"""
from typing import Optional, Dict, Any
from database.db import (
    get_user_by_username,
    verify_password,
    get_beneficiary_details,
    get_dealer_details,
    get_beneficiary_by_card,
    get_connection
)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify credentials and return user context dictionary or None. Supports username or Ration Card Number."""
    clean_identifier = username.strip()
    user = get_user_by_username(clean_identifier)
    
    # If not found by username, check if the identifier is a Ration Card Number
    if not user:
        ben_row = get_beneficiary_by_card(clean_identifier)
        if ben_row:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM users WHERE id = ?", (ben_row["user_id"],))
                user = cur.fetchone()

    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    context = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user["phone"] or "9876543210"
    }

    # Attach role specific IDs
    if user["role"] == "beneficiary":
        ben = get_beneficiary_details(user["id"])
        if ben:
            context["beneficiary_id"] = ben["id"]
            context["ration_card_number"] = ben["ration_card_number"]
            context["card_type"] = ben["card_type"]
            context["shop_id"] = ben["shop_id"]
            context["shop_name"] = ben["shop_name"]
            context["shop_number"] = ben["shop_number"]
            context["head_of_family"] = ben["head_of_family"]
            context["family_members_count"] = ben["family_members_count"]
            context["address"] = ben["address"]
            context["phone"] = ben["phone"] or context["phone"]
            context["taluk"] = ben["taluk"]
            context["district"] = ben["district"]
            context["monthly_rice_quota_kg"] = ben["monthly_rice_quota_kg"]
            context["monthly_wheat_quota_kg"] = ben["monthly_wheat_quota_kg"]
            context["monthly_sugar_quota_kg"] = ben["monthly_sugar_quota_kg"]
            context["quota_rice_kg"] = ben["monthly_rice_quota_kg"]
            context["quota_wheat_kg"] = ben["monthly_wheat_quota_kg"]
            context["quota_sugar_kg"] = ben["monthly_sugar_quota_kg"]

    elif user["role"] == "dealer":
        dealer = get_dealer_details(user["id"])
        if dealer:
            context["dealer_id"] = dealer["id"]
            context["shop_id"] = dealer["shop_id"]
            context["shop_name"] = dealer["shop_name"]
            context["shop_number"] = dealer["shop_number"]
            context["license_number"] = dealer["license_number"]
            context["counters_count"] = dealer["counters_count"]
            context["staff_count"] = dealer["staff_count"]

    return context

