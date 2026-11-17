"""
Smart Ration and Distribution System - Application Configuration
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
DATABASE_DIR = BASE_DIR / "database"

# Database Configuration
DB_PATH = DATABASE_DIR / "smart_ration.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"

# Data Files
RAW_DATASET_PATH = RAW_DATA_DIR / "smart_ration_ml_dataset.csv"
PROCESSED_DATASET_PATH = PROCESSED_DATA_DIR / "smart_ration_dataset_v2.csv"
EDA_SUMMARY_PATH = REPORTS_DIR / "eda_summary.json"

# Model Artifact Paths
CROWD_MODEL_PATH = MODELS_DIR / "crowd_model.joblib"
RICE_MODEL_PATH = MODELS_DIR / "rice_model.joblib"
WHEAT_MODEL_PATH = MODELS_DIR / "wheat_model.joblib"
SUGAR_MODEL_PATH = MODELS_DIR / "sugar_model.joblib"
WAITING_TIME_MODEL_PATH = MODELS_DIR / "waiting_time_model.joblib"
METRICS_REPORT_PATH = REPORTS_DIR / "model_evaluation_metrics.json"

# Commodity Default Entitlements (per beneficiary transaction in kg)
COMMODITY_QUOTAS = {
    "Rice": {"avg_kg": 4.5, "price_per_kg": 2.0},
    "Wheat": {"avg_kg": 2.5, "price_per_kg": 3.0},
    "Sugar": {"avg_kg": 1.0, "price_per_kg": 13.5},
}

# Operational Time Slots
OPERATIONAL_SLOTS = ["9-10 AM", "10-11 AM", "11-12 PM", "12-1 PM", "4-5 PM", "5-6 PM", "6-7 PM"]
SLOT_HOUR_MAP = {
    "9-10 AM": 9,
    "10-11 AM": 10,
    "11-12 PM": 11,
    "12-1 PM": 12,
    "4-5 PM": 16,
    "5-6 PM": 17,
    "6-7 PM": 18
}

DEFAULT_SLOT_CAPACITY = 30
LOW_STOCK_THRESHOLD_PCT = 25.0  # Alert when remaining stock < 25% of baseline or demand exceeds stock

# SMTP & Real-Time Communication Configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_SENDER_EMAIL = os.environ.get("SMTP_SENDER_EMAIL", "pds.notifications@smartration.gov.in")
SMTP_SENDER_NAME = "Smart Ration Public Distribution System"

# SMS Gateway Configuration (Fast2SMS for India, Twilio for Global)
FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY", "")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")

# Ensure required directories exist
for p in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, MODELS_DIR, DATABASE_DIR]:
    p.mkdir(parents=True, exist_ok=True)

