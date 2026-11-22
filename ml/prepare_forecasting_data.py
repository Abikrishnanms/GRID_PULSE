"""
GridPulse - Machine Learning Dataset Preprocessing
Member 3 Contribution: Energy Consumption Forecasting

This script prepares the daily energy consumption dataset for ML modeling.
Target variable: energy_per_household_kwh
"""

from pathlib import Path
import pandas as pd


def prepare_forecasting_dataset(
    input_csv_path: str = "dashboards/react-dashboard/public/data/daily_energy_summary.csv",
    output_csv_path: str = "ml/prepared_daily_energy.csv",
) -> pd.DataFrame:
    print("=" * 60)
    print("GRIDPULSE ML: STEP 2 - FORECASTING DATASET PREPARATION")
    print("=" * 60)

    # 1. Load the original raw summary dataset
    input_path = Path(input_csv_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at: {input_path}")

    print(f"Loading raw data from: {input_path}")
    df = pd.read_csv(input_path)
    initial_row_count = len(df)
    print(f"Initial records loaded: {initial_row_count}")

    # 2. Parse date column and sort chronologically
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 3. Exclude the truncated/partial final observation (2014-02-28)
    cutoff_date = pd.to_datetime("2014-02-28")
    before_filter_count = len(df)
    df = df[df["date"] < cutoff_date].copy()
    excluded_count = before_filter_count - len(df)
    print(f"Excluded {excluded_count} truncated observation (2014-02-28).")
    print(f"Remaining continuous valid records: {len(df)}")

    # 4. Check for duplicate dates
    duplicate_count = df["date"].duplicated().sum()
    print(f"Duplicate dates check: {duplicate_count} found.")

    # 5. Check for missing dates in the time sequence
    full_date_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
    missing_dates = full_date_range.difference(df["date"])
    print(f"Missing dates check: {len(missing_dates)} missing days.")

    # 6. Create Calendar Features
    df["day_of_week"] = df["date"].dt.day_of_week  # 0=Monday, 6=Sunday
    df["month"] = df["date"].dt.month              # 1-12
    df["day_of_year"] = df["date"].dt.day_of_year  # 1-366
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)  # 1 for Sat/Sun, 0 otherwise

    # 7. Create Historical Lag and Rolling Features (past observations only - zero data leakage)
    target_col = "energy_per_household_kwh"

    # Lag 1: yesterday's consumption
    df["lag_1"] = df[target_col].shift(1)

    # Lag 7: consumption from the exact same day last week
    df["lag_7"] = df[target_col].shift(7)

    # Rolling 7-day average: average of past 7 days, excluding today (shift 1 first)
    df["rolling_mean_7"] = df[target_col].shift(1).rolling(window=7).mean()

    # 8. Handle initial rows where lag features are not yet available
    # The first 7 days will have NaN for lag_7 and rolling_mean_7
    unfiltered_len = len(df)
    df_clean = df.dropna(subset=["lag_1", "lag_7", "rolling_mean_7"]).reset_index(drop=True)
    dropped_initial_lags = unfiltered_len - len(df_clean)
    print(f"Handled initial lag warmup: dropped first {dropped_initial_lags} rows with incomplete lag history.")

    # 9. Save prepared dataset to ml/ directory
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Format date back to standard string format YYYY-MM-DD for clean saving
    df_clean_to_save = df_clean.copy()
    df_clean_to_save["date"] = df_clean_to_save["date"].dt.strftime("%Y-%m-%d")
    df_clean_to_save.to_csv(output_path, index=False)
    print(f"Prepared dataset successfully saved to: {output_path}")

    # 10. Summary Report
    print("-" * 60)
    print("DATASET SUMMARY:")
    print(f"  • Date Range: {df_clean_to_save['date'].min()} to {df_clean_to_save['date'].max()}")
    print(f"  • Total Usable Rows: {len(df_clean_to_save)}")
    print(f"  • Target Variable: {target_col}")
    print(f"  • Target Mean: {df_clean[target_col].mean():.3f} kWh")
    print(f"  • Target Min: {df_clean[target_col].min():.3f} kWh | Max: {df_clean[target_col].max():.3f} kWh")
    print(f"  • Feature Columns ({len(df_clean_to_save.columns)} total):")
    for col in df_clean_to_save.columns:
        print(f"      - {col} ({df_clean_to_save[col].dtype})")
    print("-" * 60)
    print("First 3 sample rows:")
    print(df_clean_to_save[["date", target_col, "day_of_week", "month", "lag_1", "lag_7", "rolling_mean_7"]].head(3))
    print("-" * 60)

    return df_clean_to_save


if __name__ == "__main__":
    prepare_forecasting_dataset()
