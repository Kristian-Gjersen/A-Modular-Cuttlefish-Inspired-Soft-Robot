from pathlib import Path

import numpy as np
import pandas as pd


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data" / "Turn Test"

MODE_ORDER = ["Head Steering", "One Fin Drive", "Differential Drive"]
M_TO_CM = 100


def mode_from_filename(path):
    name = path.stem
    for mode in MODE_ORDER:
        if name.startswith(mode.replace(" ", "_")):
            return mode
    return None


def trial_from_filename(path):
    parts = path.stem.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return 0


def endpoint_metrics(path):
    mode = mode_from_filename(path)
    if mode is None:
        return None

    df = pd.read_csv(path)
    required = {"time_s", "x_m", "y_m"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path.name}: {sorted(missing)}")

    for column in ["time_s", "x_m", "y_m"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["time_s", "x_m", "y_m"]).sort_values("time_s")
    if len(df) < 2:
        return None

    duration_s = float(df["time_s"].iloc[-1] - df["time_s"].iloc[0])
    if duration_s <= 0:
        return None

    final_x_cm = float((df["x_m"].iloc[-1] - df["x_m"].iloc[0]) * M_TO_CM)
    final_y_cm = float((df["y_m"].iloc[-1] - df["y_m"].iloc[0]) * M_TO_CM)

    endpoint_angle_deg = float(np.degrees(np.arctan2(final_y_cm, final_x_cm)))
    if endpoint_angle_deg < 0:
        endpoint_angle_deg += 360

    endpoint_distance_cm = float(np.hypot(final_x_cm, final_y_cm))
    denominator = 2 * np.sin(np.radians(abs(endpoint_angle_deg)))
    endpoint_turning_radius_cm = np.nan
    if endpoint_distance_cm > 0 and abs(denominator) > 1e-9:
        endpoint_turning_radius_cm = endpoint_distance_cm / denominator

    return {
        "mode": mode,
        "trial": trial_from_filename(path),
        "duration_s": duration_s,
        "final_x_cm": final_x_cm,
        "final_y_cm": final_y_cm,
        "endpoint_angle_deg": endpoint_angle_deg,
        "endpoint_angle_deg_per_s": endpoint_angle_deg / duration_s,
        "endpoint_distance_cm": endpoint_distance_cm,
        "endpoint_turning_radius_cm": endpoint_turning_radius_cm,
    }


def load_trials():
    rows = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        row = endpoint_metrics(path)
        if row is not None:
            rows.append(row)

    if not rows:
        raise FileNotFoundError(f"No turn CSV files found in {DATA_DIR}")

    trials = pd.DataFrame(rows)
    order = {mode: index for index, mode in enumerate(MODE_ORDER)}
    trials["mode_order"] = trials["mode"].map(order).fillna(99)
    return trials.sort_values(["mode_order", "trial"]).drop(columns="mode_order").reset_index(drop=True)


def summarize_trials(trials):
    summary = (
        trials.groupby("mode", as_index=False)
        .agg(
            n_trials=("trial", "count"),
            mean_duration_s=("duration_s", "mean"),
            std_duration_s=("duration_s", "std"),
            mean_endpoint_angle_deg=("endpoint_angle_deg", "mean"),
            std_endpoint_angle_deg=("endpoint_angle_deg", "std"),
            mean_endpoint_angle_deg_per_s=("endpoint_angle_deg_per_s", "mean"),
            std_endpoint_angle_deg_per_s=("endpoint_angle_deg_per_s", "std"),
            mean_endpoint_turning_radius_cm=("endpoint_turning_radius_cm", "mean"),
            std_endpoint_turning_radius_cm=("endpoint_turning_radius_cm", "std"),
        )
    )
    order = {mode: index for index, mode in enumerate(MODE_ORDER)}
    summary["mode_order"] = summary["mode"].map(order).fillna(99)
    return summary.sort_values("mode_order").drop(columns="mode_order").reset_index(drop=True)


def print_results(summary, trials):
    display = summary[
        [
            "mode",
            "n_trials",
            "mean_endpoint_angle_deg",
            "std_endpoint_angle_deg",
            "mean_endpoint_angle_deg_per_s",
            "std_endpoint_angle_deg_per_s",
            "mean_duration_s",
        ]
    ].copy()

    for column in display.columns:
        if column not in {"mode", "n_trials"}:
            display[column] = display[column].map(lambda value: f"{value:.3f}" if pd.notna(value) else "")

    print("Average of 3 trials per mode")
    print(display.to_string(index=False))
    print()

    by_trial = trials[
        [
            "mode",
            "trial",
            "duration_s",
            "endpoint_angle_deg",
            "endpoint_angle_deg_per_s",
            "final_x_cm",
            "final_y_cm",
        ]
    ].copy()
    for column in ["duration_s", "endpoint_angle_deg", "endpoint_angle_deg_per_s", "final_x_cm", "final_y_cm"]:
        by_trial[column] = by_trial[column].map(lambda value: f"{value:.3f}" if pd.notna(value) else "")

    print("Individual trials")
    print(by_trial.to_string(index=False))


def main():
    trials = load_trials()
    summary = summarize_trials(trials)
    print_results(summary, trials)


if __name__ == "__main__":
    main()
