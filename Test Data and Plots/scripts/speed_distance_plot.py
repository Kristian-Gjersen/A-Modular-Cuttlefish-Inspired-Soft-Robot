from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data" / "Speed Tests"

FINISH_DISTANCE_CM = 80
DUTIES_TO_PLOT = [50, 75, 100]
DISTANCE_GRID_CM = np.linspace(0, FINISH_DISTANCE_CM, 161)

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


def load_trials():
    trials = []

    for path in sorted(DATA_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        required = {"fin", "speed", "trial", "t_downsampled", "progress_percent"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {path.name}: {sorted(missing)}")

        df = df.copy()
        df["time_s"] = pd.to_numeric(df["t_downsampled"], errors="coerce")
        df["progress_percent"] = pd.to_numeric(df["progress_percent"], errors="coerce")
        df = df.dropna(subset=["time_s", "progress_percent"])
        if df.empty:
            continue

        fin = clean_fin_name(df["fin"].iloc[0])
        duty = int(df["speed"].iloc[0])
        trial = int(df["trial"].iloc[0])

        df = df.sort_values("time_s")
        df["time_s"] = df["time_s"] - float(df["time_s"].iloc[0])
        df["distance_cm"] = df["progress_percent"].clip(0, 100) / 100 * FINISH_DISTANCE_CM

        start = pd.DataFrame({"time_s": [0.0], "distance_cm": [0.0]})
        clean = pd.concat([start, df[["time_s", "distance_cm"]]], ignore_index=True)
        clean["distance_cm"] = clean["distance_cm"].cummax()
        clean = clean.drop_duplicates("distance_cm", keep="first")

        if clean["distance_cm"].iloc[-1] < FINISH_DISTANCE_CM:
            continue

        time_at_distance = np.interp(DISTANCE_GRID_CM, clean["distance_cm"], clean["time_s"])
        trials.append(
            pd.DataFrame(
                {
                    "fin": fin,
                    "duty": duty,
                    "trial": trial,
                    "distance_cm": DISTANCE_GRID_CM,
                    "time_s": time_at_distance,
                }
            )
        )

    if not trials:
        raise FileNotFoundError(f"No usable speed CSV files found in {DATA_DIR}")

    return pd.concat(trials, ignore_index=True)


def summarize_trials(trials):
    return (
        trials.groupby(["duty", "fin", "distance_cm"], as_index=False)
        .agg(mean_time_s=("time_s", "mean"), std_time_s=("time_s", "std"), n=("trial", "count"))
    )


def plot_speed_distance(summary):
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

    for ax, duty in zip(axes, DUTIES_TO_PLOT):
        duty_data = summary[summary["duty"] == duty]

        for fin in FIN_ORDER:
            subset = duty_data[duty_data["fin"] == fin].sort_values("distance_cm")
            if subset.empty:
                continue

            ax.plot(
                subset["mean_time_s"],
                subset["distance_cm"],
                color=FIN_COLORS[fin],
                linewidth=2.4,
                label=fin,
            )

        ax.axhline(FINISH_DISTANCE_CM, color="0.35", linestyle="--", linewidth=1.2)
        ax.set_title(f"{duty}% duty")
        ax.set_xlabel("Time (s)")
        ax.set_ylim(0, FINISH_DISTANCE_CM + 5)
        ax.set_xlim(left=0)
        ax.grid(True, alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="both", width=1.1, length=5)

    axes[0].set_ylabel("Distance (cm)")
    axes[-1].legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return fig


def main():
    figure = plot_speed_distance(summarize_trials(load_trials()))
    plt.show()


if __name__ == "__main__":
    main()
