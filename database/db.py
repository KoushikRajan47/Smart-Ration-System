"""
Database management, connection handling, and data access layer for Smart Ration System.
"""
import sqlite3
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from config.settings import DB_PATH, SCHEMA_PATH

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Securely hash password with SHA-256 and salt."""
    if not salt:
        salt = "SmartRationSalt2025"
    salted = f"{salt}:{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()

def verify_password(password: str, hashed: str, salt: Optional[str] = None) -> bool:
    """Verify raw password against stored hash."""
    return hash_password(password, salt) == hashed

class SmartRow(dict):
    """
    Enhanced SQLite row that supports dictionary key access,
    safe .get(key, default) access, integer index access (row[0]), and standard dict methods.
    Completely eliminates 'sqlite3.Row object has no attribute get' across all modules.
    """
    def __init__(self, cursor: sqlite3.Cursor, row: tuple):
        super().__init__({col[0]: row[idx] for idx, col in enumerate(cursor.description)})
        self._raw_tuple = tuple(row)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return self._raw_tuple[key]
        return super().__getitem__(key)

def get_connection() -> sqlite3.Connection:
    """Return an active SQLite connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = SmartRow
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(force: bool = False) -> None:
    """Initialize SQLite database using schema.sql."""
    if force and DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except Exception:
            pass

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()

# --- User & Auth Queries ---

def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

def create_user(username: str, raw_password: str, role: str, full_name: str, email: str = "", phone: str = "") -> int:
    pwd_hash = hash_password(raw_password)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (username, password_hash, role, full_name, email, phone)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, pwd_hash, role, full_name, email, phone)
        )
        conn.commit()
        return cursor.lastrowid

# --- Beneficiary Queries ---

def get_beneficiary_details(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT b.*, u.username, u.full_name, u.email, s.shop_name, s.shop_number, s.taluk, s.district
               FROM beneficiaries b
               JOIN users u ON b.user_id = u.id
               JOIN ration_shops s ON b.shop_id = s.id
               WHERE b.user_id = ?""",
            (user_id,)
        )
        return cursor.fetchone()

def get_beneficiary_by_card(ration_card_number: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT b.*, u.username, u.full_name, u.email, s.shop_name, s.shop_number
               FROM beneficiaries b
               JOIN users u ON b.user_id = u.id
               JOIN ration_shops s ON b.shop_id = s.id
               WHERE b.ration_card_number = ?""",
            (ration_card_number,)
        )
        return cursor.fetchone()

def list_all_beneficiaries(shop_id: Optional[int] = None) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if shop_id:
            cursor.execute(
                """SELECT b.*, u.username, u.full_name, s.shop_number
                   FROM beneficiaries b
                   JOIN users u ON b.user_id = u.id
                   JOIN ration_shops s ON b.shop_id = s.id
                   WHERE b.shop_id = ? ORDER BY b.id ASC""",
                (shop_id,)
            )
        else:
            cursor.execute(
                """SELECT b.*, u.username, u.full_name, s.shop_number
                   FROM beneficiaries b
                   JOIN users u ON b.user_id = u.id
                   JOIN ration_shops s ON b.shop_id = s.id
                   ORDER BY b.id ASC"""
            )
        return cursor.fetchall()

# --- Dealer & Shop Queries ---

def get_dealer_details(user_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT d.*, u.username, u.full_name, u.email, s.shop_name, s.shop_number,
                      s.address as shop_address, s.taluk, s.district, s.registered_beneficiaries,
                      s.staff_count, s.counters_count
               FROM dealers d
               JOIN users u ON d.user_id = u.id
               JOIN ration_shops s ON d.shop_id = s.id
               WHERE d.user_id = ?""",
            (user_id,)
        )
        return cursor.fetchone()

def get_all_shops() -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ration_shops ORDER BY shop_number ASC")
        return cursor.fetchall()

def get_shop_by_id(shop_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ration_shops WHERE id = ?", (shop_id,))
        return cursor.fetchone()

# --- Inventory Queries ---

def get_shop_inventory(shop_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT i.*, c.name as commodity_name, c.code as commodity_code, c.unit, c.unit_price
               FROM inventory i
               JOIN commodities c ON i.commodity_id = c.id
               WHERE i.shop_id = ?
               ORDER BY c.id ASC""",
            (shop_id,)
        )
        return cursor.fetchall()

def update_stock(shop_id: int, commodity_code: str, change_amount_kg: float, change_type: str, remarks: str = "") -> bool:
    """Safely adjust stock with transactional logging."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT i.id, i.current_stock_kg, c.id as comm_id
               FROM inventory i
               JOIN commodities c ON i.commodity_id = c.id
               WHERE i.shop_id = ? AND c.code = ?""",
            (shop_id, commodity_code)
        )
        row = cursor.fetchone()
        if not row:
            return False

        inv_id, current_stock, comm_id = row["id"], row["current_stock_kg"], row["comm_id"]
        new_stock = max(0.0, current_stock + change_amount_kg)

        cursor.execute(
            "UPDATE inventory SET current_stock_kg = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?",
            (new_stock, inv_id)
        )
        cursor.execute(
            """INSERT INTO stock_logs (shop_id, commodity_id, change_type, quantity_kg, previous_stock_kg, new_stock_kg, remarks)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (shop_id, comm_id, change_type, abs(change_amount_kg), current_stock, new_stock, remarks)
        )
        conn.commit()
        return True

# --- Slot Capacity & Booking Queries ---

def get_or_create_slot_capacity(shop_id: int, date_str: str, time_slot: str, default_cap: int = 30) -> sqlite3.Row:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM slot_capacity WHERE shop_id = ? AND date = ? AND time_slot = ?",
            (shop_id, date_str, time_slot)
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                """INSERT INTO slot_capacity (shop_id, date, time_slot, max_capacity, booked_count, is_open)
                   VALUES (?, ?, ?, ?, 0, 1)""",
                (shop_id, date_str, time_slot, default_cap)
            )
            conn.commit()
            cursor.execute("SELECT * FROM slot_capacity WHERE id = ?", (cursor.lastrowid,))
            row = cursor.fetchone()
        return row

def get_day_slot_capacities(shop_id: int, date_str: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM slot_capacity WHERE shop_id = ? AND date = ? ORDER BY id ASC",
            (shop_id, date_str)
        )
        return cursor.fetchall()

def create_booking(beneficiary_id: int, shop_id: int, date_str: str, time_slot: str, predicted_wait: float = 0.0) -> Tuple[bool, str]:
    """Atomic slot booking with capacity check."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check if beneficiary already booked for this date
        cursor.execute(
            "SELECT id FROM bookings WHERE beneficiary_id = ? AND date = ? AND status = 'CONFIRMED'",
            (beneficiary_id, date_str)
        )
        if cursor.fetchone():
            return False, "You already have an active booking for this date."

        # Check slot capacity
        cap_row = get_or_create_slot_capacity(shop_id, date_str, time_slot)
        if not cap_row["is_open"]:
            return False, f"Time slot {time_slot} is closed for bookings."
        if cap_row["booked_count"] >= cap_row["max_capacity"]:
            return False, f"Time slot {time_slot} is fully booked (capacity {cap_row['max_capacity']})."

        # Create booking ref
        import uuid
        ref = f"BK-{date_str.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}"
        cursor.execute(
            """INSERT INTO bookings (booking_reference, beneficiary_id, shop_id, date, time_slot, status, predicted_waiting_time)
               VALUES (?, ?, ?, ?, ?, 'CONFIRMED', ?)""",
            (ref, beneficiary_id, shop_id, date_str, time_slot, predicted_wait)
        )
        cursor.execute(
            "UPDATE slot_capacity SET booked_count = booked_count + 1 WHERE id = ?",
            (cap_row["id"],)
        )

        # Notify beneficiary
        cursor.execute("SELECT user_id, head_of_family FROM beneficiaries WHERE id = ?", (beneficiary_id,))
        b_info = cursor.fetchone()
        if b_info:
            cursor.execute(
                """INSERT INTO notifications (user_id, title, message, channel)
                   VALUES (?, 'Slot Booking Confirmation', ?, 'SMS')""",
                (b_info["user_id"], f"Booking Confirmed! Ref: {ref} for {date_str} at {time_slot}. Est. wait: {predicted_wait:.1f} mins.")
            )

        conn.commit()
        return True, ref

def cancel_booking(booking_id: int, beneficiary_id: int) -> Tuple[bool, str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM bookings WHERE id = ? AND beneficiary_id = ? AND status = 'CONFIRMED'",
            (booking_id, beneficiary_id)
        )
        row = cursor.fetchone()
        if not row:
            return False, "Booking not found or not in confirmed status."

        cursor.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = ?", (booking_id,))
        cursor.execute(
            """UPDATE slot_capacity SET booked_count = MAX(0, booked_count - 1)
               WHERE shop_id = ? AND date = ? AND time_slot = ?""",
            (row["shop_id"], row["date"], row["time_slot"])
        )

        # Notify beneficiary of cancellation
        cursor.execute("SELECT user_id, head_of_family FROM beneficiaries WHERE id = ?", (beneficiary_id,))
        b_info = cursor.fetchone()
        if b_info:
            cursor.execute(
                """INSERT INTO notifications (user_id, title, message, channel)
                   VALUES (?, 'Booking Cancellation Confirmation', ?, 'SMS')""",
                (b_info["user_id"], f"Booking {row['booking_reference']} on {row['date']} ({row['time_slot']}) has been cancelled. Time slot released.")
            )

        conn.commit()
        return True, "Booking cancelled successfully. Your time slot has been released."

def get_beneficiary_bookings(beneficiary_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT b.*, s.shop_name, s.shop_number
               FROM bookings b
               JOIN ration_shops s ON b.shop_id = s.id
               WHERE b.beneficiary_id = ?
               ORDER BY b.date DESC, b.id DESC""",
            (beneficiary_id,)
        )
        return cursor.fetchall()

def get_shop_bookings_for_date(shop_id: int, date_str: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT b.*, bn.ration_card_number, bn.head_of_family, bn.card_type
               FROM bookings b
               JOIN beneficiaries bn ON b.beneficiary_id = bn.id
               WHERE b.shop_id = ? AND b.date = ?
               ORDER BY b.time_slot ASC, b.id ASC""",
            (shop_id, date_str)
        )
        return cursor.fetchall()

# --- Transaction Queries ---

def record_transaction(
    beneficiary_id: int,
    shop_id: int,
    date_str: str,
    rice_kg: float,
    wheat_kg: float,
    sugar_kg: float,
    booking_id: Optional[int] = None,
    payment_mode: str = "SUBSIDIZED_FREE",
    dealer_user_id: Optional[int] = None,
    remarks: str = ""
) -> Tuple[bool, str]:
    """Execute ration collection transaction and deduct shop inventory."""
    import uuid
    tx_ref = f"TX-{date_str.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}"

    with get_connection() as conn:
        cursor = conn.cursor()

        # Compute price from commodities
        cursor.execute("SELECT code, unit_price FROM commodities")
        prices = {r["code"]: r["unit_price"] for r in cursor.fetchall()}
        total_amount = (
            rice_kg * prices.get("RICE", 0.0) +
            wheat_kg * prices.get("WHEAT", 0.0) +
            sugar_kg * prices.get("SUGAR", 0.0)
        )

        # Insert transaction
        cursor.execute(
            """INSERT INTO transactions
               (transaction_ref, booking_id, beneficiary_id, shop_id, transaction_date,
                rice_collected_kg, wheat_collected_kg, sugar_collected_kg, total_amount, payment_mode, dealer_user_id, remarks)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tx_ref, booking_id, beneficiary_id, shop_id, date_str, rice_kg, wheat_kg, sugar_kg, total_amount, payment_mode, dealer_user_id, remarks)
        )

        # Mark booking as collected if provided
        if booking_id:
            cursor.execute("UPDATE bookings SET status = 'COLLECTED' WHERE id = ?", (booking_id,))

        # Deduct inventory
        for code, qty in [("RICE", rice_kg), ("WHEAT", wheat_kg), ("SUGAR", sugar_kg)]:
            if qty > 0:
                cursor.execute(
                    """SELECT i.id, i.current_stock_kg, c.id as comm_id
                       FROM inventory i JOIN commodities c ON i.commodity_id = c.id
                       WHERE i.shop_id = ? AND c.code = ?""",
                    (shop_id, code)
                )
                row = cursor.fetchone()
                if row:
                    new_stk = max(0.0, row["current_stock_kg"] - qty)
                    cursor.execute("UPDATE inventory SET current_stock_kg = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?", (new_stk, row["id"]))
                    cursor.execute(
                        """INSERT INTO stock_logs (shop_id, commodity_id, change_type, quantity_kg, previous_stock_kg, new_stock_kg, remarks)
                           VALUES (?, ?, 'DISBURSED', ?, ?, ?, ?)""",
                        (shop_id, row["comm_id"], qty, row["current_stock_kg"], new_stk, f"Disbursed via {tx_ref}")
                    )

        # Notify beneficiary of ration collection
        cursor.execute("SELECT user_id, head_of_family, ration_card_number FROM beneficiaries WHERE id = ?", (beneficiary_id,))
        b_info = cursor.fetchone()
        if b_info:
            cursor.execute(
                """INSERT INTO notifications (user_id, title, message, channel)
                   VALUES (?, 'Ration Collection Acknowledgment', ?, 'SMS')""",
                (b_info["user_id"], f"Ration Disbursed! Ref: {tx_ref}. Collected: Rice {rice_kg}kg, Wheat {wheat_kg}kg, Sugar {sugar_kg}kg. Amount: Rs {total_amount:.2f}.")
            )

        conn.commit()
        return True, tx_ref

def get_beneficiary_transactions(beneficiary_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT t.*, s.shop_name, s.shop_number
               FROM transactions t
               JOIN ration_shops s ON t.shop_id = s.id
               WHERE t.beneficiary_id = ?
               ORDER BY t.transaction_date DESC, t.id DESC""",
            (beneficiary_id,)
        )
        return cursor.fetchall()

def get_shop_transactions(shop_id: int, limit: int = 100) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT t.*, b.ration_card_number, b.head_of_family, b.card_type
               FROM transactions t
               JOIN beneficiaries b ON t.beneficiary_id = b.id
               WHERE t.shop_id = ?
               ORDER BY t.transaction_date DESC, t.id DESC
               LIMIT ?""",
            (shop_id, limit)
        )
        return cursor.fetchall()

# --- Prediction & Telemetry Logging ---

def log_prediction(
    shop_id: int,
    prediction_date: str,
    time_slot: str,
    customers: float,
    rice_demand: float,
    wheat_demand: float,
    sugar_demand: float,
    waiting_time: float,
    model_version: str = "v1.0.0",
    notes: str = ""
) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO prediction_logs
               (shop_id, prediction_date, time_slot, predicted_customers, predicted_rice_demand,
                predicted_wheat_demand, predicted_sugar_demand, predicted_waiting_time, model_version, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (shop_id, prediction_date, time_slot, customers, rice_demand, wheat_demand, sugar_demand, waiting_time, model_version, notes)
        )
        conn.commit()

def get_recent_prediction_logs(shop_id: Optional[int] = None, limit: int = 50) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if shop_id:
            cursor.execute(
                "SELECT * FROM prediction_logs WHERE shop_id = ? ORDER BY timestamp DESC LIMIT ?",
                (shop_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM prediction_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        return cursor.fetchall()

# --- Full-Stack Enhancements: Citizen Self-Registration, Notifications, and Receipts ---

def register_new_beneficiary(
    username: str,
    raw_password: str,
    full_name: str,
    email: str,
    phone: str,
    ration_card_number: str,
    card_type: str,
    head_of_family: str,
    family_members_count: int,
    shop_id: int,
    address: str
) -> Tuple[bool, str]:
    """Register a new citizen, create login credentials, and assign statutory entitlement quotas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username.strip(),))
        if cursor.fetchone():
            return False, f"Username '{username}' is already taken."

        cursor.execute("SELECT id FROM beneficiaries WHERE ration_card_number = ?", (ration_card_number.strip(),))
        if cursor.fetchone():
            return False, f"Ration Card Number '{ration_card_number}' is already registered in the system."

        # Compute statutory quota
        if card_type == "AAY":
            rice_quota, wheat_quota, sugar_quota = 35.0, 15.0, 3.0
        elif card_type == "PHH":
            rice_quota = max(15.0, family_members_count * 5.0)
            wheat_quota = max(5.0, family_members_count * 2.5)
            sugar_quota = 2.0
        else:  # NPHH
            rice_quota, wheat_quota, sugar_quota = 10.0, 5.0, 1.0

        pwd_hash = hash_password(raw_password)
        cursor.execute(
            """INSERT INTO users (username, password_hash, role, full_name, email, phone)
               VALUES (?, ?, 'beneficiary', ?, ?, ?)""",
            (username.strip(), pwd_hash, full_name.strip(), email.strip(), phone.strip())
        )
        new_user_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO beneficiaries
               (user_id, ration_card_number, card_type, head_of_family, family_members_count, shop_id, address, phone,
                monthly_rice_quota_kg, monthly_wheat_quota_kg, monthly_sugar_quota_kg, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (new_user_id, ration_card_number.strip(), card_type, head_of_family.strip(),
             family_members_count, shop_id, address.strip(), phone.strip(),
             rice_quota, wheat_quota, sugar_quota)
        )
        ben_id = cursor.lastrowid

        # Add welcome SMS notification
        cursor.execute(
            """INSERT INTO notifications (user_id, title, message, channel)
               VALUES (?, 'Welcome to Smart Ration System', ?, 'SMS')""",
            (new_user_id, f"Dear {head_of_family}, your ration card {ration_card_number} ({card_type}) is registered at Shop #{shop_id}. You can now book collection slots online.")
        )

        conn.commit()
        return True, f"Registration successful! Your ration card {ration_card_number} is now active."

def create_notification(user_id: int, title: str, message: str, channel: str = "SMS") -> None:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notifications (user_id, title, message, channel) VALUES (?, ?, ?, ?)",
                (user_id, title, message, channel)
            )
            conn.commit()
    except Exception:
        pass

def get_user_notifications(user_id: int, limit: int = 20) -> List[sqlite3.Row]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            return cursor.fetchall()
    except Exception:
        return []

def get_transaction_by_ref(tx_ref: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT t.*, b.ration_card_number, b.head_of_family, b.card_type, b.phone,
                      s.shop_name, s.shop_number, s.address as shop_address, s.taluk, s.district
               FROM transactions t
               JOIN beneficiaries b ON t.beneficiary_id = b.id
               JOIN ration_shops s ON t.shop_id = s.id
               WHERE t.transaction_ref = ?""",
            (tx_ref.strip(),)
        )
        return cursor.fetchone()

def get_all_complaints() -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT c.*, b.ration_card_number, b.head_of_family, s.shop_name, s.shop_number
               FROM complaints c
               JOIN beneficiaries b ON c.beneficiary_id = b.id
               JOIN ration_shops s ON c.shop_id = s.id
               ORDER BY c.created_at DESC"""
        )
        return cursor.fetchall()

def resolve_complaint(complaint_id: int, notes: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE complaints SET status = 'RESOLVED', resolution_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (notes, complaint_id)
        )
        conn.commit()
        return True

def get_beneficiary_complaints(beneficiary_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT c.*, s.shop_name, s.shop_number
               FROM complaints c
               JOIN ration_shops s ON c.shop_id = s.id
               WHERE c.beneficiary_id = ?
               ORDER BY c.created_at DESC""",
            (beneficiary_id,)
        )
        return cursor.fetchall()

def get_beneficiary_monthly_usage(beneficiary_id: int, year_month: Optional[str] = None) -> Dict[str, float]:
    """Return total rice, wheat, and sugar collected by beneficiary for the specified month (default current YYYY-MM)."""
    from datetime import date
    ym = year_month or date.today().strftime("%Y-%m")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT
                COALESCE(SUM(rice_collected_kg), 0.0) as rice_collected,
                COALESCE(SUM(wheat_collected_kg), 0.0) as wheat_collected,
                COALESCE(SUM(sugar_collected_kg), 0.0) as sugar_collected
               FROM transactions
               WHERE beneficiary_id = ? AND strftime('%Y-%m', transaction_date) = ?""",
            (beneficiary_id, ym)
        )
        row = cursor.fetchone()
        if row:
            return {
                "rice_collected": float(row["rice_collected"]),
                "wheat_collected": float(row["wheat_collected"]),
                "sugar_collected": float(row["sugar_collected"]),
                "year_month": ym
            }
        return {"rice_collected": 0.0, "wheat_collected": 0.0, "sugar_collected": 0.0, "year_month": ym}



