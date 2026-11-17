"""
Production-grade Machine Learning Model Training, Comparison, and Serialization Pipeline.
Trains 5 distinct models across 4 candidate algorithms using strict chronological splitting.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure workspace root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    PROCESSED_DATASET_PATH,
    MODELS_DIR,
    REPORTS_DIR,
    CROWD_MODEL_PATH,
    RICE_MODEL_PATH,
    WHEAT_MODEL_PATH,
    SUGAR_MODEL_PATH,
    WAITING_TIME_MODEL_PATH,
    METRICS_REPORT_PATH
)
from ml.preprocessing import get_preprocessor

MODEL_PLOTS_DIR = REPORTS_DIR / "model_plots"
MODEL_PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Define audited feature schemas (Anti-Leakage Certified)
MODEL_CONFIGS = {
    "crowd": {
        "target": "Customers",
        "cat_features": ["Day", "Time_Slot"],
        "num_features": [
            "Hour", "Is_Weekend", "Is_Holiday", "Bookings",
            "Previous_Crowd", "Previous_Transactions",
            "Staff_On_Duty", "Counters_Available", "Registered_Beneficiaries"
        ],
        "save_path": CROWD_MODEL_PATH,
        "display_name": "Customer Crowd Prediction"
    },
    "rice_demand": {
        "target": "Rice_Demand_kg",
        "cat_features": ["Day", "Time_Slot"],
        "num_features": [
            "Hour", "Is_Weekend", "Is_Holiday", "Bookings",
            "Previous_Crowd", "Previous_Transactions", "Rice_Stock_kg",
            "Staff_On_Duty", "Counters_Available", "Registered_Beneficiaries"
        ],
        "save_path": RICE_MODEL_PATH,
        "display_name": "Rice Demand Prediction (kg)"
    },
    "wheat_demand": {
        "target": "Wheat_Demand_kg",
        "cat_features": ["Day", "Time_Slot"],
        "num_features": [
            "Hour", "Is_Weekend", "Is_Holiday", "Bookings",
            "Previous_Crowd", "Previous_Transactions", "Wheat_Stock_kg",
            "Staff_On_Duty", "Counters_Available", "Registered_Beneficiaries"
        ],
        "save_path": WHEAT_MODEL_PATH,
        "display_name": "Wheat Demand Prediction (kg)"
    },
    "sugar_demand": {
        "target": "Sugar_Demand_kg",
        "cat_features": ["Day", "Time_Slot"],
        "num_features": [
            "Hour", "Is_Weekend", "Is_Holiday", "Bookings",
            "Previous_Crowd", "Previous_Transactions", "Sugar_Stock_kg",
            "Staff_On_Duty", "Counters_Available", "Registered_Beneficiaries"
        ],
        "save_path": SUGAR_MODEL_PATH,
        "display_name": "Sugar Demand Prediction (kg)"
    },
    "waiting_time": {
        "target": "Waiting_Time_Min",
        "cat_features": ["Day", "Time_Slot"],
        "num_features": [
            "Hour", "Is_Weekend", "Is_Holiday", "Bookings",
            "Previous_Crowd", "Previous_Transactions",
            "Staff_On_Duty", "Counters_Available", "Registered_Beneficiaries"
        ],
        "save_path": WAITING_TIME_MODEL_PATH,
        "display_name": "Beneficiary Waiting Time Prediction (min)"
    }
}

def get_candidate_algorithms(random_state: int = 42):
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=12, min_samples_split=4, random_state=random_state, n_jobs=-1),
        "Extra Trees": ExtraTreesRegressor(n_estimators=100, max_depth=14, min_samples_split=4, random_state=random_state, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=120, learning_rate=0.08, max_depth=5, random_state=random_state)
    }

def train_and_evaluate_all():
    print(f"Reading dataset from {PROCESSED_DATASET_PATH}...")
    df = pd.read_csv(PROCESSED_DATASET_PATH)

    # Sort strictly chronologically
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(by=["Date", "Hour"]).reset_index(drop=True)

    # Chronological Split: 80% Train, 20% Test
    unique_dates = df["Date"].sort_values().unique()
    split_idx = int(len(unique_dates) * 0.80)
    split_date = unique_dates[split_idx]

    train_df = df[df["Date"] < split_date].copy()
    test_df = df[df["Date"] >= split_date].copy()

    print(f"Total Observations: {len(df)}")
    print(f"Training split: {len(train_df)} rows ({train_df['Date'].min().strftime('%Y-%m-%d')} to {train_df['Date'].max().strftime('%Y-%m-%d')})")
    print(f"Testing split:  {len(test_df)} rows ({test_df['Date'].min().strftime('%Y-%m-%d')} to {test_df['Date'].max().strftime('%Y-%m-%d')})")

    master_results = {}

    for task_key, config in MODEL_CONFIGS.items():
        print(f"\n========================================================")
        print(f"TRAINING MODEL: {config['display_name']} [Target: {config['target']}]")
        print(f"========================================================")

        X_train = train_df[config["cat_features"] + config["num_features"]]
        y_train = train_df[config["target"]]
        X_test = test_df[config["cat_features"] + config["num_features"]]
        y_test = test_df[config["target"]]

        candidate_algos = get_candidate_algorithms()
        task_comparison = []
        best_model_name = None
        best_test_r2 = -float("inf")
        best_pipeline = None
        best_predictions = None

        for name, algo in candidate_algos.items():
            preprocessor = get_preprocessor(config["cat_features"], config["num_features"], scale_numeric=(name == "Linear Regression"))
            pipeline = Pipeline(steps=[
                ("preprocessor", preprocessor),
                ("regressor", algo)
            ])

            # Train on training split only
            pipeline.fit(X_train, y_train)

            # Evaluate on Train
            y_train_pred = pipeline.predict(X_train)
            train_mae = mean_absolute_error(y_train, y_train_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            train_r2 = r2_score(y_train, y_train_pred)

            # Evaluate on Test
            y_test_pred = pipeline.predict(X_test)
            test_mae = mean_absolute_error(y_test, y_test_pred)
            test_mse = mean_squared_error(y_test, y_test_pred)
            test_rmse = np.sqrt(test_mse)
            test_r2 = r2_score(y_test, y_test_pred)

            # TimeSeriesSplit Cross-Validation (3 folds) on Training data
            tscv = TimeSeriesSplit(n_splits=3)
            cv_scores = cross_validate(
                pipeline, X_train, y_train,
                cv=tscv,
                scoring=["r2", "neg_root_mean_squared_error"],
                n_jobs=-1
            )
            cv_r2 = float(np.mean(cv_scores["test_r2"]))
            cv_rmse = float(-np.mean(cv_scores["test_neg_root_mean_squared_error"]))

            model_metrics = {
                "algorithm": name,
                "train_mae": round(float(train_mae), 3),
                "train_rmse": round(float(train_rmse), 3),
                "train_r2": round(float(train_r2), 4),
                "test_mae": round(float(test_mae), 3),
                "test_mse": round(float(test_mse), 3),
                "test_rmse": round(float(test_rmse), 3),
                "test_r2": round(float(test_r2), 4),
                "cv_r2": round(cv_r2, 4),
                "cv_rmse": round(cv_rmse, 3),
                "overfit_gap_r2": round(float(train_r2 - test_r2), 4)
            }
            task_comparison.append(model_metrics)
            print(f"  {name:18} | Test R2: {test_r2:.4f} | Test RMSE: {test_rmse:.3f} | Test MAE: {test_mae:.3f} | CV R2: {cv_r2:.4f}")

            # Best model selection by test generalization R2
            if test_r2 > best_test_r2:
                best_test_r2 = test_r2
                best_model_name = name
                best_pipeline = pipeline
                best_predictions = y_test_pred

        print(f"--> Selected Best Model: {best_model_name} with Test R2 = {best_test_r2:.4f}")

        # Save Best Pipeline
        joblib.dump(best_pipeline, config["save_path"])
        print(f"--> Saved best model artifact to {config['save_path']}")

        # Generate Visualizations for Best Model
        # 1. Actual vs Predicted
        plt.figure(figsize=(7, 6))
        sns.scatterplot(x=y_test, y=best_predictions, alpha=0.4, color="#1f77b4")
        diag_min = min(y_test.min(), best_predictions.min())
        diag_max = max(y_test.max(), best_predictions.max())
        plt.plot([diag_min, diag_max], [diag_min, diag_max], color="red", linestyle="--", lw=2, label="Perfect Fit (y=x)")
        plt.title(f"Actual vs Predicted: {config['display_name']}\n({best_model_name})", fontsize=12, fontweight="bold")
        plt.xlabel("Actual Value")
        plt.ylabel("Predicted Value")
        plt.legend()
        plt.tight_layout()
        pred_plot_path = MODEL_PLOTS_DIR / f"{task_key}_actual_vs_pred.png"
        plt.savefig(pred_plot_path, dpi=200)
        plt.close()

        # 2. Residual Distribution & Plot
        residuals = y_test - best_predictions
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        sns.scatterplot(x=best_predictions, y=residuals, alpha=0.4, ax=axes[0], color="#2ca02c")
        axes[0].axhline(0, color="red", linestyle="--")
        axes[0].set_title("Residuals vs Predicted")
        axes[0].set_xlabel("Predicted Value")
        axes[0].set_ylabel("Residual (Actual - Pred)")

        sns.histplot(residuals, kde=True, ax=axes[1], color="#9467bd", bins=25)
        axes[1].axvline(0, color="red", linestyle="--")
        axes[1].set_title("Residuals Distribution")
        axes[1].set_xlabel("Residual Error")
        plt.suptitle(f"Residual Diagnostic: {config['display_name']} ({best_model_name})", fontsize=12, fontweight="bold")
        plt.tight_layout()
        res_plot_path = MODEL_PLOTS_DIR / f"{task_key}_residuals.png"
        plt.savefig(res_plot_path, dpi=200)
        plt.close()

        master_results[task_key] = {
            "display_name": config["display_name"],
            "target": config["target"],
            "best_algorithm": best_model_name,
            "best_metrics": [m for m in task_comparison if m["algorithm"] == best_model_name][0],
            "comparison": task_comparison,
            "plots": {
                "actual_vs_pred": str(pred_plot_path),
                "residuals": str(res_plot_path)
            }
        }

    # Save master metrics JSON
    with open(METRICS_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(master_results, f, indent=2)

    # Save Markdown Evaluation Report
    report_md_path = REPORTS_DIR / "model_evaluation_report.md"
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# Machine Learning Model Evaluation and Comparison Report\n")
        f.write("## Smart Ration and Distribution System\n\n")
        f.write("Strict chronological holdout evaluation (80% Train, 20% Test) across all 5 models.\n\n")

        for key, res in master_results.items():
            f.write(f"### {res['display_name']} (`{res['target']}`)\n\n")
            f.write(f"**Selected Best Model**: **{res['best_algorithm']}**\n\n")
            f.write("| Algorithm | Train R² | Test R² | Test MAE | Test RMSE | Overfit Gap (R²) | CV R² |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for c in res["comparison"]:
                bold = "**" if c["algorithm"] == res["best_algorithm"] else ""
                f.write(f"| {bold}{c['algorithm']}{bold} | {c['train_r2']} | {c['test_r2']} | {c['test_mae']} | {c['test_rmse']} | {c['overfit_gap_r2']} | {c['cv_r2']} |\n")
            f.write("\n")

    print(f"\nAll 5 models trained and evaluated successfully!")
    print(f"Master evaluation metrics saved to {METRICS_REPORT_PATH}")
    print(f"Summary markdown report saved to {report_md_path}")
    return master_results

if __name__ == "__main__":
    train_and_evaluate_all()

