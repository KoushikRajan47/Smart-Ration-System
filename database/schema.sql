-- ====================================================================
-- SMART RATION SYSTEM - RELATIONAL DATABASE SCHEMA (SQLite3)
-- Compliant with ACID transactions, strict relational integrity,
-- indexed queries, and normalized PDS entity structures.
-- ====================================================================

PRAGMA foreign_keys = ON;

-- 1. USERS & AUTHENTICATION TABLE
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('beneficiary', 'dealer', 'admin')),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. RATION SHOPS TABLE
CREATE TABLE IF NOT EXISTS ration_shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_number TEXT UNIQUE NOT NULL,
    shop_name TEXT NOT NULL,
    address TEXT NOT NULL,
    taluk TEXT NOT NULL,
    district TEXT NOT NULL,
    registered_beneficiaries INTEGER NOT NULL DEFAULT 850,
    staff_count INTEGER NOT NULL DEFAULT 3,
    counters_count INTEGER NOT NULL DEFAULT 2,
    contact_number TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. DEALERS TABLE
CREATE TABLE IF NOT EXISTS dealers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    shop_id INTEGER NOT NULL,
    license_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE
);

-- 4. BENEFICIARIES (RATION CARD HOLDERS)
CREATE TABLE IF NOT EXISTS beneficiaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    ration_card_number TEXT UNIQUE NOT NULL,
    card_type TEXT NOT NULL CHECK(card_type IN ('AAY', 'PHH', 'NPHH')),
    head_of_family TEXT NOT NULL,
    family_members_count INTEGER NOT NULL DEFAULT 4,
    shop_id INTEGER NOT NULL,
    address TEXT,
    phone TEXT,
    monthly_rice_quota_kg REAL NOT NULL DEFAULT 20.0,
    monthly_wheat_quota_kg REAL NOT NULL DEFAULT 10.0,
    monthly_sugar_quota_kg REAL NOT NULL DEFAULT 2.0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE
);

-- 5. COMMODITIES TABLE
CREATE TABLE IF NOT EXISTS commodities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'kg',
    unit_price REAL NOT NULL DEFAULT 0.0,
    safety_stock_threshold_kg REAL NOT NULL DEFAULT 100.0,
    description TEXT
);

-- 6. INVENTORY (PER SHOP & COMMODITY)
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    commodity_id INTEGER NOT NULL,
    current_stock_kg REAL NOT NULL DEFAULT 0.0,
    safety_threshold_kg REAL NOT NULL DEFAULT 100.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(shop_id, commodity_id),
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE,
    FOREIGN KEY (commodity_id) REFERENCES commodities(id) ON DELETE CASCADE
);

-- 7. STOCK MOVEMENT LOGS
CREATE TABLE IF NOT EXISTS stock_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    commodity_id INTEGER NOT NULL,
    change_type TEXT NOT NULL CHECK(change_type IN ('INFLOW', 'DISBURSED', 'ADJUSTMENT')),
    quantity_kg REAL NOT NULL,
    previous_stock_kg REAL NOT NULL,
    new_stock_kg REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE,
    FOREIGN KEY (commodity_id) REFERENCES commodities(id) ON DELETE CASCADE
);

-- 8. TIME SLOT CAPACITIES
CREATE TABLE IF NOT EXISTS slot_capacity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    max_capacity INTEGER NOT NULL DEFAULT 30,
    booked_count INTEGER NOT NULL DEFAULT 0,
    is_open INTEGER NOT NULL DEFAULT 1,
    UNIQUE(shop_id, date, time_slot),
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE
);

-- 9. BOOKINGS TABLE
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference TEXT UNIQUE NOT NULL,
    beneficiary_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK(status IN ('CONFIRMED', 'COLLECTED', 'CANCELLED', 'EXPIRED')),
    predicted_waiting_time REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE
);

-- 10. TRANSACTIONS / DISTRIBUTION RECORDS
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_ref TEXT UNIQUE NOT NULL,
    booking_id INTEGER,
    beneficiary_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    transaction_date TEXT NOT NULL,
    rice_collected_kg REAL NOT NULL DEFAULT 0.0,
    wheat_collected_kg REAL NOT NULL DEFAULT 0.0,
    sugar_collected_kg REAL NOT NULL DEFAULT 0.0,
    total_amount REAL NOT NULL DEFAULT 0.0,
    payment_mode TEXT NOT NULL DEFAULT 'CASH' CHECK(payment_mode IN ('CASH', 'UPI', 'SUBSIDIZED_FREE')),
    dealer_user_id INTEGER,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE SET NULL,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE,
    FOREIGN KEY (dealer_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 11. COMPLAINTS & FEEDBACK TABLE
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    beneficiary_id INTEGER NOT NULL,
    shop_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE
);

-- 12. PREDICTION LOGS (AUDITING & TELEMETRY)
CREATE TABLE IF NOT EXISTS prediction_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shop_id INTEGER NOT NULL,
    prediction_date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    predicted_customers REAL NOT NULL,
    predicted_rice_demand REAL NOT NULL,
    predicted_wheat_demand REAL NOT NULL,
    predicted_sugar_demand REAL NOT NULL,
    predicted_waiting_time REAL NOT NULL,
    model_version TEXT NOT NULL DEFAULT 'v1.0.0',
    notes TEXT,
    FOREIGN KEY (shop_id) REFERENCES ration_shops(id) ON DELETE CASCADE
);

-- 13. NOTIFICATIONS TABLE (SMS / ALERTS DISPATCH)
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'SMS',
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- PERFORMANCE INDICES
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_beneficiaries_card ON beneficiaries(ration_card_number);
CREATE INDEX IF NOT EXISTS idx_bookings_date_slot ON bookings(shop_id, date, time_slot);
CREATE INDEX IF NOT EXISTS idx_bookings_beneficiary ON bookings(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(shop_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_inventory_shop ON inventory(shop_id);

