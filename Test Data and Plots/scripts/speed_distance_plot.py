from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data" / "Speed Tests"

FINISH_DISTANCE_CM = 80
DUTIES_TO_PLOT = [50, 75, 100]

FIN_ORDER = ["Pink Fin", "Purple Fin", "Blue Fin"]
FIN_COLORS = {
    "Pink Fin": "#efa0c6",
    "Purple Fin": "#7374b6",
    "Blue Fin": "#37a1d9",
}


def clean_fin_name(value):
    text = str(value).strip().lower()
    if "pink" in text:
        return "Pink Fin"
    if "purple" in text:
        return "Purple Fin"
    if "blue" in text:
        return "Blue Fin"
    return str(value).strip()


def load_raw_trials():
    """Load the recorded observations without resampling or smoothing them."""
    trials = []

    for path in sorted(DATA_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        required = {"fin", "speed", "trial", "t_downsampled"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {path.name}: {sorted(missing)}")

        velocity_column = next(
            (column for column in ("vx_median", "v_{x}_median") if column in df.columns),
            None,
        )
        if velocity_column is None:
            raise ValueError(
                f"Missing velocity column in {path.name}: expected vx_median or v_{{x}}_median"
            )

        df = df.copy()
        df["time_s"] = pd.to_numeric(df["t_downsampled"], errors="coerce")
        df["velocity_m_s"] = pd.to_numeric(df[velocity_column], errors="coerce")
        df = df.dropna(subset=["time_s", "velocity_m_s"]).sort_values("time_s")
        if df.empty:
            continue

        df["time_s"] -= df["time_s"].iloc[0]
        time_s = df["time_s"].to_numpy()
        velocity_m_s = df["velocity_m_s"].to_numpy()
        distance_m = np.concatenate(
            ([0.0], np.cumsum(np.diff(time_s) * (velocity_m_s[1:] + velocity_m_s[:-1]) / 2))
        )

        df["distance_cm"] = np.maximum.accumulate(distance_m * 100)

        finish_rows = np.flatnonzero(df["distance_cm"].to_numpy() >= FINISH_DISTANCE_CM)
        if not len(finish_rows):
            continue

        finish_row = finish_rows[0]
        df = df.iloc[: finish_row + 1].copy()
        if finish_row > 0:
            previous_distance = distance_m[finish_row - 1] * 100
            crossing_distance = distance_m[finish_row] * 100
            fraction = (FINISH_DISTANCE_CM - previous_distance) / (
                crossing_distance - previous_distance
            )
            df.iloc[-1, df.columns.get_loc("time_s")] = (
                time_s[finish_row - 1] + fraction * (time_s[finish_row] - time_s[finish_row - 1])
            )
        df.iloc[-1, df.columns.get_loc("distance_cm")] = FINISH_DISTANCE_CM

        df["fin"] = clean_fin_name(df["fin"].iloc[0])
        df["duty"] = int(df["speed"].iloc[0])
        df["trial"] = int(df["trial"].iloc[0])

        trials.append(df[["fin", "duty", "trial", "time_s", "distance_cm"]])

    if not trials:
        raise FileNotFoundError(f"No usable speed CSV files found in {DATA_DIR}")

    return pd.concat(trials, ignore_index=True)


def plot_speed_distance(trials):
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "mathtext.fontset": "dejavuserif",
            "axes.labelsize": 16,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 13,
        }
    )

    fig, axes = plt.subplots(1, len(DUTIES_TO_PLOT), figsize=(13, 4.8), sharey=True)
    if len(DUTIES_TO_PLOT) == 1:
        axes = [axes]

    plotted_trials = trials[trials["duty"].isin(DUTIES_TO_PLOT)]
    max_time_s = plotted_trials["time_s"].max()
    max_distance_cm = plotted_trials["distance_cm"].max()
    y_upper_cm = max(FINISH_DISTANCE_CM + 5, max_distance_cm + 5)
    time_grid_s = np.linspace(0, max_time_s, 161)

    for ax, duty in zip(axes, DUTIES_TO_PLOT):
        duty_data = trials[trials["duty"] == duty]

        for fin in FIN_ORDER:
            fin_data = duty_data[duty_data["fin"] == fin]
            distance_by_trial = []
            for _, trial_data in fin_data.groupby("trial"):
                trial_data = (
                    trial_data.sort_values("time_s")
                    .drop_duplicates("time_s", keep="last")
                )
                distance = np.interp(
                    time_grid_s,
                    trial_data["time_s"],
                    trial_data["distance_cm"],
                )
                distance_by_trial.append(distance)

            if distance_by_trial:
                mean_distance = np.mean(np.vstack(distance_by_trial), axis=0)
                finish_rows = np.flatnonzero(mean_distance >= FINISH_DISTANCE_CM)
                if not len(finish_rows):
                    continue

                finish_row = finish_rows[0]
                plot_time_s = time_grid_s[: finish_row + 1].copy()
                plot_distance_cm = mean_distance[: finish_row + 1].copy()
                if finish_row > 0:
                    previous_distance = mean_distance[finish_row - 1]
                    fraction = (FINISH_DISTANCE_CM - previous_distance) / (
                        mean_distance[finish_row] - previous_distance
                    )
                    plot_time_s[-1] = time_grid_s[finish_row - 1] + fraction * (
                        time_grid_s[finish_row] - time_grid_s[finish_row - 1]
                    )
                plot_distance_cm[-1] = FINISH_DISTANCE_CM
                ax.plot(
                    plot_time_s,
                    plot_distance_cm,
                    color=FIN_COLORS[fin],
                    linewidth=2.4,
                    label=fin,
                )

        ax.axhline(FINISH_DISTANCE_CM, color="0.35", linestyle="--", linewidth=1.2)
        ax.set_title(f"{duty}% duty")
        ax.set_xlabel("Time (s)")
        ax.set_ylim(0, y_upper_cm)
        ax.set_xlim(0, max_time_s)
        ax.grid(True, alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="both", width=1.1, length=5)

    axes[0].set_ylabel("Distance (cm)")
    axes[-1].legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return fig


def main():
    plot_speed_distance(load_raw_trials())
    plt.show()


if __name__ == "__main__":
    main()
