"""
Automated unit tests for SQLite database operations, transactions, and security.
"""
import pytest
import sqlite3
import uuid
from pathlib import Path
import sys

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import (
    init_db,
    get_connection,
    hash_password,
    verify_password,
    create_user,
    get_user_by_username,
    register_new_beneficiary,
    get_or_create_slot_capacity,
    create_booking,
    cancel_booking,
    update_stock,
    record_transaction,
    get_shop_inventory
)

@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database schema is ready."""
    init_db(force=False)

def test_password_hashing():
    raw_pwd = "SecretPassword123"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert len(hashed) == 64  # SHA-256 length
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_user_creation_and_retrieval():
    unique_user = f"testuser_{uuid.uuid4().hex[:6]}"
    uid = create_user(
        username=unique_user,
        raw_password="TestPassword@2025",
        role="beneficiary",
        full_name="Test User",
        email=f"{unique_user}@test.com"
    )
    assert uid > 0

    fetched = get_user_by_username(unique_user)
    assert fetched is not None
    assert fetched["username"] == unique_user
    assert verify_password("TestPassword@2025", fetched["password_hash"]) is True

def test_slot_capacity_and_atomic_booking():
    test_hex = uuid.uuid4().hex[:8]
    rc_num = f"RC-SLOT-{test_hex.upper()}"
    u_name = f"test_slot_user_{test_hex}"
    ok_reg, msg_reg = register_new_beneficiary(
        username=u_name,
        raw_password="TestPassword@2025",
        full_name="Test Slot Beneficiary",
        email=f"test_slot_{test_hex}@example.com",
        phone="9988776655",
        ration_card_number=rc_num,
        card_type="PHH",
        head_of_family="Test Slot Beneficiary",
        family_members_count=4,
        shop_id=1,
        address="Test Address, Bengaluru"
    )
    assert ok_reg is True

    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM beneficiaries WHERE ration_card_number = ?", (rc_num,))
        test_ben_id = c.fetchone()["id"]

    date_str = f"2099-01-{int(test_hex[:2], 16) % 28 + 1:02d}"
    slot = "10-11 AM"

    try:
        # Reset any prior slot capacity for this test date
        with get_connection() as conn:
            conn.execute("DELETE FROM bookings WHERE shop_id = 1 AND date = ?", (date_str,))
            conn.execute("DELETE FROM slot_capacity WHERE shop_id = 1 AND date = ?", (date_str,))
            conn.commit()

        cap = get_or_create_slot_capacity(shop_id=1, date_str=date_str, time_slot=slot, default_cap=10)
        assert cap["max_capacity"] >= 10

        # Book slot
        ok, ref = create_booking(beneficiary_id=test_ben_id, shop_id=1, date_str=date_str, time_slot=slot, predicted_wait=6.5)
        assert ok is True
        assert ref.startswith("BK-")

        # Attempt duplicate booking on same date
        ok2, msg2 = create_booking(beneficiary_id=test_ben_id, shop_id=1, date_str=date_str, time_slot="11-12 PM")
        assert ok2 is False
        assert "already have an active booking" in msg2
    finally:
        # Clean up test rows
        with get_connection() as conn:
            conn.execute("DELETE FROM bookings WHERE beneficiary_id = ?", (test_ben_id,))
            conn.execute("DELETE FROM slot_capacity WHERE shop_id = 1 AND date = ?", (date_str,))
            conn.execute("DELETE FROM beneficiaries WHERE id = ?", (test_ben_id,))
            conn.execute("DELETE FROM users WHERE username = ?", (u_name,))
            conn.commit()

def test_stock_update_and_inventory():
    shop_id = 1
    comm_code = "RICE"

    inv_before = get_shop_inventory(shop_id)
    rice_before = [i["current_stock_kg"] for i in inv_before if i["commodity_code"] == comm_code][0]

    try:
        # Add 100 kg
        ok = update_stock(shop_id, comm_code, 100.0, "INFLOW", "Test depot receipt")
        assert ok is True

        inv_after = get_shop_inventory(shop_id)
        rice_after = [i["current_stock_kg"] for i in inv_after if i["commodity_code"] == comm_code][0]
        assert rice_after == rice_before + 100.0
    finally:
        # Revert 100 kg back to maintain original baseline
        update_stock(shop_id, comm_code, -100.0, "ADJUSTMENT", "Test revert baseline")

if __name__ == "__main__":
    pytest.main(["-v", __file__])
