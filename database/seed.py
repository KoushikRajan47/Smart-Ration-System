"""
Database seeding script.
Fills the SQLite database with realistic PDS demo data,
including hashed credentials, shops, inventory, beneficiaries, and transaction logs.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ensure root workspace is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import OPERATIONAL_SLOTS
from database.db import (
    init_db,
    get_connection,
    create_user,
    create_booking,
    record_transaction
)

def seed_database():
    print("Initializing fresh database schema...")
    init_db(force=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Insert Commodities
        commodities = [
            ("RICE", "Subsidized Parboiled Rice", "kg", 2.0, 150.0, "Essential staple grain under NFSA"),
            ("WHEAT", "Fortified Whole Wheat", "kg", 3.0, 80.0, "High nutrition fortified wheat grain"),
            ("SUGAR", "Refined White Sugar", "kg", 13.5, 40.0, "Subsidized cane sugar per household")
        ]
        cursor.executemany(
            """INSERT INTO commodities (code, name, unit, unit_price, safety_stock_threshold_kg, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            commodities
        )

        # 2. Insert Ration Shops
        shops = [
            ("SHOP-KA-001", "Jayanagar Fair Price Depot #42", "4th Block, 11th Main, Jayanagar", "Bengaluru South", "Bengaluru Urban", 850, 3, 2, "080-26589901"),
            ("SHOP-KA-002", "Malleswaram Civil Supplies Center #18", "Margosa Road, Malleswaram", "Bengaluru North", "Bengaluru Urban", 920, 4, 3, "080-23348812"),
            ("SHOP-KA-003", "Indiranagar PDS Service Point #07", "100ft Road, HAL 2nd Stage", "Bengaluru East", "Bengaluru Urban", 780, 3, 2, "080-25217733")
        ]
        cursor.executemany(
            """INSERT INTO ration_shops (shop_number, shop_name, address, taluk, district, registered_beneficiaries, staff_count, counters_count, contact_number)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            shops
        )

        # 3. Insert Initial Inventory for all shops
        cursor.execute("SELECT id FROM ration_shops")
        shop_ids = [r["id"] for r in cursor.fetchall()]

        cursor.execute("SELECT id, code, safety_stock_threshold_kg FROM commodities")
        comm_rows = cursor.fetchall()
        comm_map = {r["code"]: r for r in comm_rows}

        initial_stocks = {
            1: {"RICE": 540.0, "WHEAT": 185.0, "SUGAR": 95.0},
            2: {"RICE": 620.0, "WHEAT": 210.0, "SUGAR": 115.0},
            3: {"RICE": 470.0, "WHEAT": 160.0, "SUGAR": 85.0}
        }

        for shop_id in shop_ids:
            for code, qty in initial_stocks.get(shop_id, {"RICE": 500.0, "WHEAT": 180.0, "SUGAR": 90.0}).items():
                c_id = comm_map[code]["id"]
                thresh = comm_map[code]["safety_stock_threshold_kg"]
                cursor.execute(
                    """INSERT INTO inventory (shop_id, commodity_id, current_stock_kg, safety_threshold_kg)
                       VALUES (?, ?, ?, ?)""",
                    (shop_id, c_id, qty, thresh)
                )
                cursor.execute(
                    """INSERT INTO stock_logs (shop_id, commodity_id, change_type, quantity_kg, previous_stock_kg, new_stock_kg, remarks)
                       VALUES (?, ?, 'INFLOW', ?, 0, ?, 'Initial Monthly Depot Allocation')""",
                    (shop_id, c_id, qty, qty)
                )

        conn.commit()

    # 4. Create Users and Roles
    print("Seeding users and credentials...")
    # Admin
    admin_uid = create_user("admin", "adminpassword", "admin", "PDS Divisional Director", "admin@pds.gov.in", "9845000001")

    # Dealers
    dealer1_uid = create_user("dealer1", "dealerpassword", "dealer", "Ramesh Kumar Sharma", "ramesh@fps42.in", "9845011111")
    dealer2_uid = create_user("dealer2", "dealerpassword", "dealer", "Suresh Gowda", "suresh@fps18.in", "9845022222")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dealers (user_id, shop_id, license_number, full_name, phone) VALUES (?, 1, 'PDS/BLR/2021/0491', 'Ramesh Kumar Sharma', '9845011111')", (dealer1_uid,))
        cursor.execute("INSERT INTO dealers (user_id, shop_id, license_number, full_name, phone) VALUES (?, 2, 'PDS/BLR/2020/0118', 'Suresh Gowda', '9845022222')", (dealer2_uid,))
        conn.commit()

    # Beneficiaries
    b1_uid = create_user("citizen1", "citizenpassword", "beneficiary", "Anand V. Rao", "anand.rao@email.com", "9845033331")
    b2_uid = create_user("citizen2", "citizenpassword", "beneficiary", "Lakshmi Devi", "lakshmi.d@email.com", "9845033332")
    b3_uid = create_user("citizen3", "citizenpassword", "beneficiary", "Mohammed Farooq", "farooq.m@email.com", "9845033333")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO beneficiaries (user_id, ration_card_number, card_type, head_of_family, family_members_count, shop_id, address, phone, monthly_rice_quota_kg, monthly_wheat_quota_kg, monthly_sugar_quota_kg)
               VALUES (?, 'RC-KA-99201', 'AAY', 'Anand V. Rao', 5, 1, '#12, 5th Cross, Jayanagar', '9845033331', 35.0, 15.0, 3.0)""",
            (b1_uid,)
        )
        b1_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO beneficiaries (user_id, ration_card_number, card_type, head_of_family, family_members_count, shop_id, address, phone, monthly_rice_quota_kg, monthly_wheat_quota_kg, monthly_sugar_quota_kg)
               VALUES (?, 'RC-KA-88412', 'PHH', 'Lakshmi Devi', 4, 1, '#45, 9th Main, Jayanagar', '9845033332', 20.0, 10.0, 2.0)""",
            (b2_uid,)
        )
        b2_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO beneficiaries (user_id, ration_card_number, card_type, head_of_family, family_members_count, shop_id, address, phone, monthly_rice_quota_kg, monthly_wheat_quota_kg, monthly_sugar_quota_kg)
               VALUES (?, 'RC-KA-77305', 'NPHH', 'Mohammed Farooq', 3, 2, '#78, Margosa Rd, Malleswaram', '9845033333', 10.0, 5.0, 1.0)""",
            (b3_uid,)
        )
        b3_id = cursor.lastrowid
        conn.commit()

    # 5. Seed Slot Capacities for Today and Upcoming 7 Days
    print("Seeding slot capacities and sample bookings...")
    base_date = datetime.now().date()
    with get_connection() as conn:
        cursor = conn.cursor()
        for offset in range(-2, 8):
            day_str = (base_date + timedelta(days=offset)).strftime("%Y-%m-%d")
            for shop_id in shop_ids:
                for slot in OPERATIONAL_SLOTS:
                    cursor.execute(
                        """INSERT OR IGNORE INTO slot_capacity (shop_id, date, time_slot, max_capacity, booked_count, is_open)
                           VALUES (?, ?, ?, 30, 0, 1)""",
                        (shop_id, day_str, slot)
                    )
        conn.commit()

    # 6. Seed Sample Active Booking for citizen1
    tomorrow_str = (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
    create_booking(b1_id, 1, tomorrow_str, "10-11 AM", predicted_wait=7.5)

    # 7. Seed Past Collected Transaction for citizen2
    yesterday_str = (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
    record_transaction(
        beneficiary_id=b2_id,
        shop_id=1,
        date_str=yesterday_str,
        rice_kg=20.0,
        wheat_kg=10.0,
        sugar_kg=2.0,
        payment_mode="SUBSIDIZED_FREE",
        remarks="Monthly NFSA Entitlement Collected"
    )

    print("Database seeding completed successfully!")
    print(f"Sample Login Accounts:\n"
          f"  Admin:       username='admin', password='adminpassword'\n"
          f"  Dealer:      username='dealer1', password='dealerpassword'\n"
          f"  Beneficiary: username='citizen1', password='citizenpassword'")

if __name__ == "__main__":
    seed_database()

