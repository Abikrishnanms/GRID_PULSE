"""
GridPulse - Machine Learning Model Validation & Saving
Member 3 Contribution: Energy Consumption Forecasting

Validates and persists the top-performing RandomForestRegressor model:
1. Strict 80/20 chronological split with 7 approved features (zero target leakage).
2. Reproducibility verification (random_state=42).
3. Test metrics: MAE, RMSE, MAPE, Mean Bias Error.
4. Error analysis over time and identification of under/over-prediction periods.
5. Saves model with joblib and writes metadata JSON.
"""

from datetime import datetime
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


def validate_and_save_model():
    print("=" * 65)
    print("GRIDPULSE ML: STEP 4 - BEST MODEL VALIDATION & PERSISTENCE")
    print("=" * 65)

    data_path = Path("ml/prepared_daily_energy.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Prepared dataset not found at: {data_path}")

    df = pd.read_csv(data_path)
    print(f"Loaded prepared dataset: {len(df)} rows from {df['date'].iloc[0]} to {df['date'].iloc[-1]}")

    # 1. Define target and safe feature set
    target_col = "energy_per_household_kwh"
    feature_cols = [
        "day_of_week",
        "month",
        "day_of_year",
        "is_weekend",
        "lag_1",
        "lag_7",
        "rolling_mean_7",
    ]

    print("\n[Verification Checklist]")
    print(f"  [✓] Target: '{target_col}'")
    print(f"  [✓] Feature columns (7): {feature_cols}")
    print("  [✓] Excluded target-leakage columns: total_energy_kwh, previous_observation_kwh, energy_change_*")

    # 2. Chronological 80/20 Split (no shuffling)
    train_size = int(len(df) * 0.80)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()

    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values

    print(f"  [✓] Chronological split without shuffling:")
    print(f"      - Training: {len(train_df)} rows ({train_df['date'].iloc[0]} to {train_df['date'].iloc[-1]})")
    print(f"      - Testing:  {len(test_df)} rows ({test_df['date'].iloc[0]} to {test_df['date'].iloc[-1]})")
    print("  [✓] Reproducibility: random_state=42")

    # 3. Train RandomForestRegressor
    print("\nTraining RandomForestRegressor...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=1,
    )
    rf_model.fit(X_train, y_train)

    # 4. Predict on Test Set
    y_pred = rf_model.predict(X_test)

    # 5. Calculate Metrics
    residuals = y_pred - y_test  # positive = overprediction, negative = underprediction
    abs_errors = np.abs(residuals)
    pct_errors = (abs_errors / y_test) * 100

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    mape = float(np.mean(pct_errors))
    mean_bias = float(np.mean(residuals))  # Mean Prediction Error

    print("\n" + "=" * 65)
    print("RANDOM FOREST TEST SET METRICS:")
    print(f"  • MAE (Mean Absolute Error):        {mae:.4f} kWh/household")
    print(f"  • RMSE (Root Mean Squared Error):   {rmse:.4f} kWh/household")
    print(f"  • MAPE (Mean Abs Percent Error):    {mape:.2f}%")
    print(f"  • Mean Prediction Error (Bias):     {mean_bias:+.4f} kWh/household")
    print("=" * 65)

    # 6. Save Actual vs. Predicted comparison CSV
    comparison_df = pd.DataFrame({
        "date": test_df["date"].values,
        "actual_kwh": np.round(y_test, 4),
        "predicted_kwh": np.round(y_pred, 4),
        "residual_error": np.round(residuals, 4),
        "abs_error": np.round(abs_errors, 4),
        "percentage_error": np.round(pct_errors, 2),
    })
    comparison_path = Path("ml/test_actual_vs_predicted.csv")
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\nSaved test comparison to: {comparison_path}")

    # 7. Error Analysis Over Time
    print("\n" + "-" * 65)
    print("RESIDUAL & ERROR ANALYSIS OVER TIME:")

    # Monthly breakdown on test set
    comparison_df["month_group"] = comparison_df["date"].str[:7]
    monthly_breakdown = comparison_df.groupby("month_group").agg(
        days=("actual_kwh", "count"),
        mean_actual=("actual_kwh", "mean"),
        mean_pred=("predicted_kwh", "mean"),
        mae=("abs_error", "mean"),
        mean_bias=("residual_error", "mean"),
    ).reset_index()

    print("\nMonthly Performance Breakdown (Test Period):")
    for _, row in monthly_breakdown.iterrows():
        print(f"  {row['month_group']} ({int(row['days'])} days): Actual Avg={row['mean_actual']:.2f} kWh | Pred Avg={row['mean_pred']:.2f} kWh | MAE={row['mae']:.4f} kWh | Bias={row['mean_bias']:+.4f} kWh")

    # Dates with largest absolute errors
    top_errors = comparison_df.sort_values("abs_error", ascending=False).head(5)
    print("\nTop 5 Largest Error Days (Peak Outliers):")
    for _, row in top_errors.iterrows():
        direction = "OVERPREDICTED" if row["residual_error"] > 0 else "UNDERPREDICTED"
        print(f"  • {row['date']}: Actual={row['actual_kwh']} kWh vs Pred={row['predicted_kwh']} kWh | Error={row['residual_error']:+.3f} kWh ({direction})")

    # 8. Save the Trained Model with joblib
    model_save_path = Path("ml/random_forest_forecaster.joblib")
    joblib.dump(rf_model, model_save_path)
    print(f"\n[✓] Saved trained Random Forest model to: {model_save_path}")

    # 9. Save Metadata JSON
    metadata = {
        "model_name": "RandomForestRegressor",
        "model_purpose": "Household daily energy consumption forecasting",
        "target_variable": target_col,
        "feature_names": feature_cols,
        "n_features": len(feature_cols),
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 8,
            "random_state": 42,
            "n_jobs": 1,
        },
        "training_period": {
            "start_date": train_df["date"].iloc[0],
            "end_date": train_df["date"].iloc[-1],
            "sample_count": len(train_df),
        },
        "testing_period": {
            "start_date": test_df["date"].iloc[0],
            "end_date": test_df["date"].iloc[-1],
            "sample_count": len(test_df),
        },
        "test_metrics": {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "MAPE_percent": round(mape, 2),
            "Mean_Prediction_Bias": round(mean_bias, 4),
        },
        "created_at": datetime.now().isoformat(),
    }

    metadata_path = Path("ml/model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[✓] Saved model metadata to: {metadata_path}")

    # 10. Verify Model Reloading and Test a 1-day ahead inference
    reloaded_model = joblib.load(model_save_path)
    sample_input = X_test[-1:].reshape(1, -1)
    sample_pred = float(reloaded_model.predict(sample_input)[0])
    actual_val = float(y_test[-1])
    print("\n[Verification: Reload & 1-Day Inference Test]")
    print(f"  Latest test date input ({test_df['date'].iloc[-1]}):")
    print(f"  Predicted next-day value from reloaded model: {sample_pred:.4f} kWh")
    print(f"  Actual observed value:                      {actual_val:.4f} kWh")
    print(f"  Abs difference:                             {abs(sample_pred - actual_val):.4f} kWh")
    print("=" * 65)

    return rf_model, comparison_df, metadata


if __name__ == "__main__":
    validate_and_save_model()
