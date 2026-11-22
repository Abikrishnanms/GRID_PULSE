"""
GridPulse - 30-Day Recursive Electricity Consumption Forecasting
Member 3 Contribution: Energy Consumption Forecasting

Loads the persisted RandomForestRegressor model and metadata without retraining.
Generates an out-of-sample 30-day recursive forecast starting from 2014-02-28
(the day immediately following the last clean historical date, 2014-02-27).
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd


def run_30_day_recursive_forecast(
    model_path: str = "ml/random_forest_forecaster.joblib",
    metadata_path: str = "ml/model_metadata.json",
    data_path: str = "ml/prepared_daily_energy.csv",
    output_csv_path: str = "ml/forecast_30_days.csv",
    n_days: int = 30,
):
    print("=" * 65)
    print("GRIDPULSE ML: STEP 5 - 30-DAY RECURSIVE FORECASTING")
    print("=" * 65)

    # 1. Inspect and load model and metadata
    model_file = Path(model_path)
    meta_file = Path(metadata_path)
    data_file = Path(data_path)

    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")
    if not meta_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_file}")
    if not data_file.exists():
        raise FileNotFoundError(f"Prepared data file not found: {data_file}")

    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"Loaded metadata for: {metadata.get('model_name')}")
    print(f"  • Trained on: {metadata['training_period']['sample_count']} days ({metadata['training_period']['start_date']} to {metadata['training_period']['end_date']})")
    print(f"  • Test MAE: {metadata['test_metrics']['MAE']} kWh | MAPE: {metadata['test_metrics']['MAPE_percent']}%")
    print(f"  • Feature names ({len(metadata['feature_names'])}): {metadata['feature_names']}")

    # 2. Load model with joblib (NO RETRAINING)
    model = joblib.load(model_file)
    print(f"[✓] Successfully loaded saved model from: {model_file}")

    # 3. Load historical data to construct initial lag buffer
    df = pd.read_csv(data_file)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    last_historical_date = df["date"].iloc[-1]
    print(f"\nLast clean historical observation: {last_historical_date.strftime('%Y-%m-%d')} ({last_historical_date.strftime('%A, %d %B %Y')})")
    print("NOTE: Forecasting starts strictly on the next chronological day (2014-02-28), not in 2026.")

    # We need at least the last 7 historical energy observations
    target_series = list(df["energy_per_household_kwh"].values)
    date_series = list(df["date"].values)

    # 4. Generate 30 consecutive forecast dates
    forecast_dates = pd.date_range(
        start=last_historical_date + pd.Timedelta(days=1),
        periods=n_days,
        freq="D",
    )
    print(f"Forecast Horizon: {len(forecast_dates)} days ({forecast_dates[0].strftime('%Y-%m-%d')} to {forecast_dates[-1].strftime('%Y-%m-%d')})")

    # 5. Recursive forecasting loop
    predictions = []

    print("\nExecuting recursive multi-step forecasting:")
    for step, current_date in enumerate(forecast_dates, start=1):
        # Calendar features for the future day
        day_of_week = current_date.day_of_week  # 0=Monday, 6=Sunday
        month = current_date.month              # 1-12
        day_of_year = current_date.day_of_year  # 1-366
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Lag features from past observations/predictions
        lag_1 = target_series[-1]
        lag_7 = target_series[-7]
        rolling_mean_7 = float(np.mean(target_series[-7:]))  # strictly the 7 preceding observations

        # Build feature vector matching model schema
        features_dict = {
            "day_of_week": day_of_week,
            "month": month,
            "day_of_year": day_of_year,
            "is_weekend": is_weekend,
            "lag_1": lag_1,
            "lag_7": lag_7,
            "rolling_mean_7": rolling_mean_7,
        }

        feature_vector = np.array([[features_dict[col] for col in metadata["feature_names"]]])

        # Predict next day consumption
        predicted_kwh = float(model.predict(feature_vector)[0])
        predictions.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "predicted_energy_per_household_kwh": round(predicted_kwh, 4),
        })

        # Append prediction to target_series for subsequent recursive steps
        target_series.append(predicted_kwh)
        date_series.append(current_date)

    # 6. Validate predictions
    forecast_df = pd.DataFrame(predictions)

    # Validation checks
    assert len(forecast_df) == n_days, f"Expected {n_days} rows, got {len(forecast_df)}"
    assert forecast_df["predicted_energy_per_household_kwh"].isnull().sum() == 0, "Null predictions found"
    assert (forecast_df["predicted_energy_per_household_kwh"] > 0).all(), "Non-positive predictions found"

    # Check date continuity
    parsed_dates = pd.to_datetime(forecast_df["date"])
    date_diffs = (parsed_dates - parsed_dates.shift(1))[1:]
    assert (date_diffs == pd.Timedelta(days=1)).all(), "Forecast dates are not strictly consecutive"
    print("\n[✓] Validation passed: Exactly 30 consecutive, non-null, positive daily predictions.")

    # 7. Save output CSV
    output_path = Path(output_csv_path)
    forecast_df.to_csv(output_path, index=False)
    print(f"[✓] Saved 30-day forecast to: {output_path}")

    # 8. Print complete 30-day prediction table
    print("\n" + "=" * 65)
    print("30-DAY FORECAST TABLE (2014-02-28 to 2014-03-29):")
    print(f"{'Day':<5} {'Date':<12} {'Day of Week':<12} {'Predicted (kWh/hh)':<20} {'Grid Total (~5k HH)':<20}")
    print("-" * 65)

    for i, row in forecast_df.iterrows():
        dt = pd.to_datetime(row["date"])
        day_name = dt.strftime("%A")
        kwh_hh = row["predicted_energy_per_household_kwh"]
        total_kwh = kwh_hh * 5000  # estimated for 5,000 households
        print(f"#{i+1:<4} {row['date']:<12} {day_name:<12} {kwh_hh:<20.4f} {total_kwh:<20.1f}")

    print("-" * 65)
    print(f"Summary Statistics:")
    print(f"  • 30-Day Mean:   {forecast_df['predicted_energy_per_household_kwh'].mean():.4f} kWh/household")
    print(f"  • 30-Day Min:    {forecast_df['predicted_energy_per_household_kwh'].min():.4f} kWh/household ({forecast_df.loc[forecast_df['predicted_energy_per_household_kwh'].idxmin(), 'date']})")
    print(f"  • 30-Day Max:    {forecast_df['predicted_energy_per_household_kwh'].max():.4f} kWh/household ({forecast_df.loc[forecast_df['predicted_energy_per_household_kwh'].idxmax(), 'date']})")
    print("=" * 65)

    return forecast_df


if __name__ == "__main__":
    run_30_day_recursive_forecast()
