# Exploratory Data Analysis (EDA) Report
## Smart Ration and Distribution System

- **Total Observations**: 5,110
- **Total Variables**: 23
- **Duplicate Records**: 0

### Missing Values Analysis

| Variable | Missing Count | Missing % |
|---|---|---|
| Bookings | 76 | 1.49% |
| Previous_Crowd | 61 | 1.19% |
| Previous_Transactions | 51 | 1.0% |
| Rice_Stock_kg | 40 | 0.78% |

### Descriptive Statistics (Key Variables)

| Variable | Mean | Std | Min | Median (50%) | Max |
|---|---|---|---|---|---|
| Customers | 49.07 | 16.39 | 5.0 | 48.0 | 105.0 |
| Waiting_Time_Min | 8.81 | 4.08 | 2.0 | 8.4 | 29.5 |
| Rice_Demand_kg | 181.44 | 62.64 | 13.5 | 177.55 | 468.4 |
| Wheat_Demand_kg | 74.65 | 27.06 | 8.2 | 72.3 | 199.8 |
| Sugar_Demand_kg | 25.04 | 9.25 | 3.3 | 24.2 | 62.5 |
| Rice_Stock_kg | 514.11 | 55.11 | 312.0 | 515.0 | 732.0 |
| Bookings | 11.61 | 4.04 | 1.0 | 11.0 | 28.0 |

### Key Analytical Insights

1. **Strong Footfall Predictors**: Prior crowd (`0.76` correlation), previous transactions (`0.71`), and slot bookings (`0.62`) demonstrate strong predictive power for customer volume.
2. **Peak Operating Hours**: High customer volumes cluster in mid-morning (10-11 AM) and late afternoon (5-6 PM).
3. **Staffing Impact**: Waiting times are strongly mitigated by available staff (`-0.44` correlation) and counters open.
4. **Commodity Linkage**: Hourly commodity demand strongly follows customer numbers, allowing accurate supply chain replenishment.
