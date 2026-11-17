"""
Data preparation, column alignment, and dataset synthesis module.
Produces the official 23-variable smart_ration_dataset_v2.csv
ensuring strict adherence to PDS operational physics and target integrity.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Ensure root workspace is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import RAW_DATASET_PATH, PROCESSED_DATASET_PATH

def generate_processed_dataset(seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    print(f"Loading raw dataset from {RAW_DATASET_PATH}...")
    df = pd.read_csv(RAW_DATASET_PATH)

    # 1. Standardize columns
    if "Transactions" in df.columns and "Previous_Transactions" not in df.columns:
        df["Previous_Transactions"] = df["Transactions"]

    # 2. Add Counters_Available based on Staff_On_Duty
    if "Counters_Available" not in df.columns:
        # Typically 1 supervisor + 1-3 counter operators
        counters = np.clip(df["Staff_On_Duty"] - 1, 1, 3)
        # Occasionally full staff manning counters during peak hours
        peak_mask = df["Hour"].isin([10, 11, 17])
        counters = np.where(peak_mask & (df["Staff_On_Duty"] >= 3), np.minimum(df["Staff_On_Duty"], 3), counters)
        df["Counters_Available"] = counters.astype(int)

    # 3. Commodity-specific visiting customers
    # Each customer may collect Rice, Wheat, and/or Sugar
    if "Rice_Customers" not in df.columns:
        rice_ratio = np.random.uniform(0.82, 0.94, size=len(df))
        df["Rice_Customers"] = np.clip(np.round(df["Customers"] * rice_ratio), 1, df["Customers"]).astype(int)

    if "Wheat_Customers" not in df.columns:
        wheat_ratio = np.random.uniform(0.55, 0.72, size=len(df))
        df["Wheat_Customers"] = np.clip(np.round(df["Customers"] * wheat_ratio), 0, df["Customers"]).astype(int)

    if "Sugar_Customers" not in df.columns:
        sugar_ratio = np.random.uniform(0.42, 0.60, size=len(df))
        df["Sugar_Customers"] = np.clip(np.round(df["Customers"] * sugar_ratio), 0, df["Customers"]).astype(int)

    # 4. Commodity Demands in kg
    # Average entitlement draws per customer:
    # Rice ~ 4.2 kg (std 0.4), Wheat ~ 2.4 kg (std 0.3), Sugar ~ 1.0 kg (std 0.1)
    if "Rice_Demand_kg" not in df.columns:
        rice_rates = np.random.normal(loc=4.2, scale=0.35, size=len(df))
        rice_rates = np.clip(rice_rates, 3.2, 5.2)
        df["Rice_Demand_kg"] = np.round(df["Rice_Customers"] * rice_rates, 1)

    if "Wheat_Demand_kg" not in df.columns:
        wheat_rates = np.random.normal(loc=2.4, scale=0.25, size=len(df))
        wheat_rates = np.clip(wheat_rates, 1.6, 3.2)
        df["Wheat_Demand_kg"] = np.round(df["Wheat_Customers"] * wheat_rates, 1)

    if "Sugar_Demand_kg" not in df.columns:
        sugar_rates = np.random.normal(loc=1.0, scale=0.10, size=len(df))
        sugar_rates = np.clip(sugar_rates, 0.7, 1.4)
        df["Sugar_Demand_kg"] = np.round(df["Sugar_Customers"] * sugar_rates, 1)

    # 5. Order columns according to the 23-variable specification
    expected_23_columns = [
        "Date",
        "Day",
        "Hour",
        "Time_Slot",
        "Is_Weekend",
        "Is_Holiday",
        "Bookings",
        "Previous_Crowd",
        "Previous_Transactions",
        "Staff_On_Duty",
        "Counters_Available",
        "Registered_Beneficiaries",
        "Rice_Stock_kg",
        "Wheat_Stock_kg",
        "Sugar_Stock_kg",
        "Customers",
        "Rice_Customers",
        "Wheat_Customers",
        "Sugar_Customers",
        "Rice_Demand_kg",
        "Wheat_Demand_kg",
        "Sugar_Demand_kg",
        "Waiting_Time_Min"
    ]

    # Reorder
    df = df[expected_23_columns]

    PROCESSED_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DATASET_PATH, index=False)
    print(f"Successfully generated {PROCESSED_DATASET_PATH} with shape {df.shape} and 23 columns.")
    return df

if __name__ == "__main__":
    generate_processed_dataset()

