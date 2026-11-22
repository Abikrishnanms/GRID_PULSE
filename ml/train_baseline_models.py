"""
GridPulse - Machine Learning Baseline Forecasting & Evaluation
Member 3 Contribution: Energy Consumption Forecasting

Models:
1. Seasonal Naive Baseline (using lag_7)
2. RandomForestRegressor
3. HistGradientBoostingRegressor

Evaluation Metrics: MAE, RMSE, MAPE
"""

from pathlib import Path
import numpy as np
import pandas as pd


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
    return {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 2)}


def train_and_evaluate_baselines(
    data_path: str = "ml/prepared_daily_energy.csv",
    output_eval_path: str = "ml/baseline_model_evaluation.csv",
):
    print("=" * 65)
    print("GRIDPULSE ML: STEP 3 - BASELINE MODEL DEVELOPMENT & EVALUATION")
    print("=" * 65)

    # 1. Load prepared dataset
    file_path = Path(data_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Prepared dataset not found at: {file_path}")

    df = pd.read_csv(file_path)
    print(f"Loaded prepared dataset: {len(df)} rows from {df['date'].iloc[0]} to {df['date'].iloc[-1]}")

    # 2. Define target and strictly safe feature columns (no target leakage)
    target = "energy_per_household_kwh"
    features = [
        "day_of_week",
        "month",
        "day_of_year",
        "is_weekend",
        "lag_1",
        "lag_7",
        "rolling_mean_7",
    ]

    print(f"Prediction Target: {target}")
    print(f"Selected Features ({len(features)}): {features}")

    # 3. Chronological 80/20 train/test split (no shuffling)
    train_size = int(len(df) * 0.80)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()

    X_train = train_df[features].values
    y_train = train_df[target].values
    X_test = test_df[features].values
    y_test = test_df[target].values

    print(f"\nChronological Split:")
    print(f"  • Training set: {len(train_df)} rows ({train_df['date'].iloc[0]} to {train_df['date'].iloc[-1]})")
    print(f"  • Testing set:  {len(test_df)} rows ({test_df['date'].iloc[0]} to {test_df['date'].iloc[-1]})")

    results = []

    # 4. Model 1: Seasonal Naive Baseline (predicts consumption from same day last week)
    print("\n[1/3] Evaluating Seasonal Naive Baseline (lag_7)...")
    y_pred_naive = test_df["lag_7"].values
    scores_naive = evaluate_predictions(y_test, y_pred_naive)
    results.append({"Model": "Seasonal Naive (lag_7)", **scores_naive})
    print(f"      MAE: {scores_naive['MAE']} kWh | RMSE: {scores_naive['RMSE']} kWh | MAPE: {scores_naive['MAPE']}%")

    # Check for scikit-learn
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    except ImportError:
        print("\n[!] scikit-learn is not installed in the Python environment.")
        print("    Please install it using: pip install scikit-learn")
        eval_df = pd.DataFrame(results)
        eval_df.to_csv(output_eval_path, index=False)
        print(f"\nSaved partial baseline evaluation to: {output_eval_path}")
        return eval_df, None

    # 5. Model 2: RandomForestRegressor
    print("\n[2/3] Training RandomForestRegressor...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    scores_rf = evaluate_predictions(y_test, y_pred_rf)
    results.append({"Model": "RandomForestRegressor", **scores_rf})
    print(f"      MAE: {scores_rf['MAE']} kWh | RMSE: {scores_rf['RMSE']} kWh | MAPE: {scores_rf['MAPE']}%")

    # 6. Model 3: HistGradientBoostingRegressor
    print("\n[3/3] Training HistGradientBoostingRegressor...")
    hgb_model = HistGradientBoostingRegressor(max_iter=100, max_depth=6, random_state=42)
    hgb_model.fit(X_train, y_train)
    y_pred_hgb = hgb_model.predict(X_test)
    scores_hgb = evaluate_predictions(y_test, y_pred_hgb)
    results.append({"Model": "HistGradientBoostingRegressor", **scores_hgb})
    print(f"      MAE: {scores_hgb['MAE']} kWh | RMSE: {scores_hgb['RMSE']} kWh | MAPE: {scores_hgb['MAPE']}%")

    # 7. Save evaluation results to CSV
    eval_df = pd.DataFrame(results)
    eval_df.to_csv(output_eval_path, index=False)
    print(f"\nSaved evaluation results to: {output_eval_path}")

    # 8. Best performing model
    best_model_row = eval_df.sort_values("MAE").iloc[0]
    print("=" * 65)
    print("EVALUATION SUMMARY TABLE:")
    print(eval_df.to_string(index=False))
    print("-" * 65)
    print(f"BEST PERFORMING MODEL (by Test MAE): {best_model_row['Model']}")
    print(f"  • MAE:  {best_model_row['MAE']} kWh")
    print(f"  • RMSE: {best_model_row['RMSE']} kWh")
    print(f"  • MAPE: {best_model_row['MAPE']}%")
    print("=" * 65)

    return eval_df, {"rf": rf_model, "hgb": hgb_model}


if __name__ == "__main__":
    train_and_evaluate_baselines()
