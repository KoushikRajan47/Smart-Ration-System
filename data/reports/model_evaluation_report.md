# Machine Learning Model Evaluation and Comparison Report
## Smart Ration and Distribution System

Strict chronological holdout evaluation (80% Train, 20% Test) across all 5 models.

### Customer Crowd Prediction (`Customers`)

**Selected Best Model**: **Gradient Boosting**

| Algorithm | Train R² | Test R² | Test MAE | Test RMSE | Overfit Gap (R²) | CV R² |
|---|---|---|---|---|---|---|
| Linear Regression | 0.8519 | 0.8544 | 4.884 | 6.143 | -0.0025 | 0.8482 |
| Random Forest | 0.9645 | 0.886 | 4.347 | 5.435 | 0.0785 | 0.8737 |
| Extra Trees | 0.9834 | 0.8872 | 4.334 | 5.408 | 0.0962 | 0.8789 |
| **Gradient Boosting** | 0.9265 | 0.8947 | 4.173 | 5.225 | 0.0319 | 0.8779 |

### Rice Demand Prediction (kg) (`Rice_Demand_kg`)

**Selected Best Model**: **Gradient Boosting**

| Algorithm | Train R² | Test R² | Test MAE | Test RMSE | Overfit Gap (R²) | CV R² |
|---|---|---|---|---|---|---|
| Linear Regression | 0.7866 | 0.7942 | 21.674 | 27.553 | -0.0076 | 0.7811 |
| Random Forest | 0.9458 | 0.8114 | 20.787 | 26.378 | 0.1345 | 0.7979 |
| Extra Trees | 0.9768 | 0.811 | 20.781 | 26.4 | 0.1657 | 0.802 |
| **Gradient Boosting** | 0.8846 | 0.8195 | 20.303 | 25.806 | 0.0651 | 0.7927 |

### Wheat Demand Prediction (kg) (`Wheat_Demand_kg`)

**Selected Best Model**: **Gradient Boosting**

| Algorithm | Train R² | Test R² | Test MAE | Test RMSE | Overfit Gap (R²) | CV R² |
|---|---|---|---|---|---|---|
| Linear Regression | 0.7267 | 0.7277 | 10.775 | 13.518 | -0.001 | 0.7255 |
| Random Forest | 0.9252 | 0.7382 | 10.478 | 13.254 | 0.187 | 0.7365 |
| Extra Trees | 0.9658 | 0.7326 | 10.563 | 13.397 | 0.2332 | 0.74 |
| **Gradient Boosting** | 0.8425 | 0.7444 | 10.326 | 13.097 | 0.0981 | 0.7372 |

### Sugar Demand Prediction (kg) (`Sugar_Demand_kg`)

**Selected Best Model**: **Gradient Boosting**

| Algorithm | Train R² | Test R² | Test MAE | Test RMSE | Overfit Gap (R²) | CV R² |
|---|---|---|---|---|---|---|
| Linear Regression | 0.708 | 0.719 | 3.781 | 4.784 | -0.011 | 0.7012 |
| Random Forest | 0.9159 | 0.7246 | 3.725 | 4.736 | 0.1913 | 0.704 |
| Extra Trees | 0.963 | 0.72 | 3.766 | 4.776 | 0.243 | 0.7131 |
| **Gradient Boosting** | 0.8266 | 0.7371 | 3.623 | 4.628 | 0.0895 | 0.7087 |

### Beneficiary Waiting Time Prediction (min) (`Waiting_Time_Min`)

**Selected Best Model**: **Gradient Boosting**

| Algorithm | Train R² | Test R² | Test MAE | Test RMSE | Overfit Gap (R²) | CV R² |
|---|---|---|---|---|---|---|
| Linear Regression | 0.6195 | 0.6023 | 2.024 | 2.567 | 0.0172 | 0.6126 |
| Random Forest | 0.8765 | 0.6424 | 1.959 | 2.434 | 0.2342 | 0.6334 |
| Extra Trees | 0.9338 | 0.6327 | 1.983 | 2.467 | 0.3011 | 0.6255 |
| **Gradient Boosting** | 0.7759 | 0.6588 | 1.923 | 2.378 | 0.1172 | 0.5966 |

