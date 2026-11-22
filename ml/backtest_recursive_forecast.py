"""
GridPulse - 30-Day Recursive Forecast Historical Backtesting
Member 3 Contribution: Energy Consumption Forecasting

Performs rolling-origin backtesting across multiple 30-day evaluation windows:
1. Rolling forecast origins where full 30-day actuals are known.
2. Strict recursive generation: past actuals only prior to origin; subsequent lags use predictions.
3. Calculates MAE, RMSE, MAPE, and Mean Bias overall and by horizon:
   - Days 1–7
   - Days 8–14
   - Days 15–21
   - Days 22–30
4. Saves detailed predictions and summary metrics CSVs to ml/.
5. Analyzes error accumulation over time.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd


def run_recursive_backtesting(
    model_path: str = "ml/random_forest_forecaster.joblib",
    metadata_path: str = "ml/model_metadata.json",
    data_path: str = "ml/prepared_daily_energy.csv",
    preds_output_path: str = "ml/backtesting_predictions.csv",
    metrics_output_path: str = "ml/backtesting_summary_metrics.csv",
):
    print("=" * 65)
    print("GRIDPULSE ML: STEP 6 - 30-DAY RECURSIVE FORECAST BACKTESTING")
    print("=" * 65)

    # 1. Load model, metadata, and prepared dataset
    model_file = Path(model_path)
    meta_file = Path(metadata_path)
    data_file = Path(data_path)

    if not model_file.exists() or not meta_file.exists() or not data_file.exists():
        raise FileNotFoundError("Required model, metadata, or data file missing.")

    with open(meta_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    model = joblib.load(model_file)
    df = pd.read_csv(data_file)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    print(f"Loaded model: {metadata.get('model_name')}")
    print(f"Dataset: {len(df)} days ({df['date'].iloc[0].strftime('%Y-%m-%d')} to {df['date'].iloc[-1].strftime('%Y-%m-%d')})")

    # 2. Define Rolling Forecast Origins
    # We choose 5 distinct forecast origins spanning the out-of-sample test period
    # Each origin has a complete 30-day actual future available
    origins_indices = [655, 685, 715, 745, 775]
    origins_info = []

    print("\n[Rolling Forecast Origins Selected (30-Day Horizons)]:")
    for idx in origins_indices:
        origin_date = df["date"].iloc[idx]
        eval_start = df["date"].iloc[idx + 1]
        eval_end = df["date"].iloc[idx + 30]
        origins_info.append({
            "origin_index": idx,
            "origin_date": origin_date.strftime("%Y-%m-%d"),
            "eval_start": eval_start.strftime("%Y-%m-%d"),
            "eval_end": eval_end.strftime("%Y-%m-%d"),
        })
        print(f"  • Origin {len(origins_info)}: {origin_date.strftime('%Y-%m-%d')} -> Evaluates {eval_start.strftime('%Y-%m-%d')} to {eval_end.strftime('%Y-%m-%d')} (30 days)")

    # 3. Execute Recursive Backtesting across all origins
    all_predictions = []

    for orig in origins_info:
        orig_idx = orig["origin_index"]
        orig_date_str = orig["origin_date"]

        # Only history available UP TO origin date
        history = list(df["energy_per_household_kwh"].iloc[:orig_idx + 1].values)

        for h in range(1, 31):
            target_idx = orig_idx + h
            target_date = df["date"].iloc[target_idx]
            actual_kwh = float(df["energy_per_household_kwh"].iloc[target_idx])

            # Features for future day
            day_of_week = target_date.day_of_week
            month = target_date.month
            day_of_year = target_date.day_of_year
            is_weekend = 1 if day_of_week in [5, 6] else 0

            # Lags drawn recursively from history buffer
            lag_1 = history[-1]
            lag_7 = history[-7]
            rolling_mean_7 = float(np.mean(history[-7:]))

            feat_dict = {
                "day_of_week": day_of_week,
                "month": month,
                "day_of_year": day_of_year,
                "is_weekend": is_weekend,
                "lag_1": lag_1,
                "lag_7": lag_7,
                "rolling_mean_7": rolling_mean_7,
            }

            feat_vector = np.array([[feat_dict[col] for col in metadata["feature_names"]]])
            pred_kwh = float(model.predict(feat_vector)[0])

            # Append prediction to history for next recursive steps
            history.append(pred_kwh)

            residual = pred_kwh - actual_kwh
            abs_err = abs(residual)
            pct_err = (abs_err / actual_kwh) * 100

            # Determine horizon group
            if h <= 7:
                h_group = "Days 1-7"
            elif h <= 14:
                h_group = "Days 8-14"
            elif h <= 21:
                h_group = "Days 15-21"
            else:
                h_group = "Days 22-30"

            all_predictions.append({
                "origin_date": orig_date_str,
                "forecast_date": target_date.strftime("%Y-%m-%d"),
                "horizon_day": h,
                "horizon_group": h_group,
                "actual_kwh": round(actual_kwh, 4),
                "predicted_kwh": round(pred_kwh, 4),
                "residual_error": round(residual, 4),
                "abs_error": round(abs_err, 4),
                "pct_error": round(pct_err, 2),
            })

    preds_df = pd.DataFrame(all_predictions)

    # 4. Save Detailed Backtesting Predictions CSV
    preds_output = Path(preds_output_path)
    preds_df.to_csv(preds_output, index=False)
    print(f"\n[✓] Saved {len(preds_df)} backtesting predictions to: {preds_output}")

    # 5. Compute Metrics: Overall and By Horizon
    def calc_metrics(sub_df: pd.DataFrame, label: str) -> dict:
        mae = float(sub_df["abs_error"].mean())
        rmse = float(np.sqrt((sub_df["residual_error"] ** 2).mean()))
        mape = float(sub_df["pct_error"].mean())
        bias = float(sub_df["residual_error"].mean())
        return {
            "Evaluation_Segment": label,
            "Sample_Days": len(sub_df),
            "MAE_kwh": round(mae, 4),
            "RMSE_kwh": round(rmse, 4),
            "MAPE_percent": round(mape, 2),
            "Mean_Bias_kwh": round(bias, 4),
        }

    summary_rows = []
    # Overall
    summary_rows.append(calc_metrics(preds_df, "Overall 30-Day Recursive"))

    # Horizons
    horizon_order = ["Days 1-7", "Days 8-14", "Days 15-21", "Days 22-30"]
    for hg in horizon_order:
        sub = preds_df[preds_df["horizon_group"] == hg]
        summary_rows.append(calc_metrics(sub, f"Horizon {hg}"))

    # Origin breakdown
    for orig in origins_info:
        sub = preds_df[preds_df["origin_date"] == orig["origin_date"]]
        summary_rows.append(calc_metrics(sub, f"Origin {orig['origin_date']} (30d)"))

    metrics_df = pd.DataFrame(summary_rows)
    metrics_output = Path(metrics_output_path)
    metrics_df.to_csv(metrics_output, index=False)
    print(f"[✓] Saved backtesting summary metrics to: {metrics_output}")

    # 6. Display Comparison & Results
    print("\n" + "=" * 65)
    print("BACKTESTING RESULTS BY HORIZON SEGMENT:")
    print(f"{'Segment':<28} {'Days':<6} {'MAE (kWh)':<12} {'RMSE (kWh)':<12} {'MAPE (%)':<10} {'Bias (kWh)':<10}")
    print("-" * 65)
    for _, r in metrics_df.iloc[:5].iterrows():
        print(f"{r['Evaluation_Segment']:<28} {r['Sample_Days']:<6} {r['MAE_kwh']:<12.4f} {r['RMSE_kwh']:<12.4f} {r['MAPE_percent']:<10.2f} {r['Mean_Bias_kwh']:<+10.4f}")

    print("\n" + "-" * 65)
    print("ORIGIN-BY-ORIGIN SUMMARY:")
    for _, r in metrics_df.iloc[5:].iterrows():
        print(f"  {r['Evaluation_Segment']}: MAE={r['MAE_kwh']} kWh | RMSE={r['RMSE_kwh']} kWh | MAPE={r['MAPE_percent']}% | Bias={r['Mean_Bias_kwh']:+0.4f} kWh")

    print("\n" + "=" * 65)
    print("1-DAY-AHEAD VS. 30-DAY RECURSIVE COMPARISON:")
    print(f"  • 1-Day-Ahead (Known True Lags):   MAE = 0.3020 kWh | RMSE = 0.3931 kWh | MAPE = 2.81%")
    print(f"  • 30-Day Recursive (Compounded):   MAE = {summary_rows[0]['MAE_kwh']} kWh | RMSE = {summary_rows[0]['RMSE_kwh']} kWh | MAPE = {summary_rows[0]['MAPE_percent']}%")
    print(f"  • Error Increase Factor:           {summary_rows[0]['MAE_kwh'] / 0.3020:.2f}x")
    print("=" * 65)

    return preds_df, metrics_df


if __name__ == "__main__":
    run_recursive_backtesting()
