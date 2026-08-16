from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data" / "Turn Test"

MODE_ORDER = ["Head Steering", "One Fin Drive", "Differential Drive"]
LINE_STYLES = {
    "Head Steering": "-",
    "One Fin Drive": (0, (6.0, 4.0)),
    "Differential Drive": (0, (1.5, 4.0)),
}
PURPLE = "#7374b6"
M_TO_CM = 100
PROGRESS_GRID = np.linspace(0, 100, 250)

LINE_WIDTH = 2.5
ARROW_COUNT = 3
ARROW_SIZE = 24
ARROW_WIDTH = 1.5
ARROW_LENGTH = 12
ARROW_WINDOW = 10
START_SIZE = 80
END_SIZE = 90


def mode_from_filename(path):
    name = path.stem
    for mode in MODE_ORDER:
        if name.startswith(mode.replace(" ", "_")):
            return mode
    return None


def trial_from_filename(path):
    match = path.stem.rsplit("_", 1)
    if len(match) == 2 and match[1].isdigit():
        return int(match[1])
    return 0


def load_tracks():
    rows = []

    for path in sorted(DATA_DIR.glob("*.csv")):
        mode = mode_from_filename(path)
        if mode is None:
            continue

        df = pd.read_csv(path)
        required = {"time_s", "x_m", "y_m"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {path.name}: {sorted(missing)}")

        for column in ["time_s", "x_m", "y_m"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.dropna(subset=["time_s", "x_m", "y_m"]).sort_values("time_s")
        if len(df) < 2:
            continue

        time = df["time_s"].to_numpy(dtype=float)
        progress = (time - time[0]) / (time[-1] - time[0]) * 100
        x_cm = (df["x_m"].to_numpy(dtype=float) - float(df["x_m"].iloc[0])) * M_TO_CM
        y_cm = (df["y_m"].to_numpy(dtype=float) - float(df["y_m"].iloc[0])) * M_TO_CM

        rows.append(
            pd.DataFrame(
                {
                    "mode": mode,
                    "trial": trial_from_filename(path),
                    "progress_percent": PROGRESS_GRID,
                    "x_cm": np.interp(PROGRESS_GRID, progress, x_cm),
                    "y_cm": np.interp(PROGRESS_GRID, progress, y_cm),
                }
            )
        )

    if not rows:
        raise FileNotFoundError(f"No turn CSV files found in {DATA_DIR}")

    return pd.concat(rows, ignore_index=True)


def averaged_tracks():
    trials = load_tracks()
    average = (
        trials.groupby(["mode", "progress_percent"], as_index=False)
        .agg(x_cm=("x_cm", "mean"), y_cm=("y_cm", "mean"), n_trials=("trial", "nunique"))
    )
    order = {mode: index for index, mode in enumerate(MODE_ORDER)}
    average["mode_order"] = average["mode"].map(order).fillna(99)
    return average.sort_values(["mode_order", "progress_percent"]).drop(columns="mode_order")


def add_direction_arrows(ax, x, y, n_arrows=ARROW_COUNT, color="black"):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        return

    arrow_indices = np.linspace(0, len(x) - 1, n_arrows + 2, dtype=int)[1:-1]
    arrow_indices = arrow_indices[1:]

    for index in arrow_indices:
        start = max(0, index - ARROW_WINDOW)
        end = min(len(x) - 1, index + ARROW_WINDOW)
        dx = x[end] - x[start]
        dy = y[end] - y[start]
        length = float(np.hypot(dx, dy))
        if length == 0:
            continue

        unit_x = dx / length
        unit_y = dy / length
        half_length = ARROW_LENGTH / 2

        ax.annotate(
            "",
            xy=(x[index] + unit_x * half_length, y[index] + unit_y * half_length),
            xytext=(x[index] - unit_x * half_length, y[index] - unit_y * half_length),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=ARROW_WIDTH,
                mutation_scale=ARROW_SIZE,
                shrinkA=0,
                shrinkB=0,
            ),
            zorder=6,
        )


def style_axis(ax):
    ax.grid(True, alpha=0.3)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.0)
    ax.tick_params(axis="both", width=1.0, length=5, pad=6)
    ax.set_aspect("equal", adjustable="box")


def plot_turn_paths(df):
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "mathtext.fontset": "dejavuserif",
            "axes.labelsize": 16,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 14,
            "lines.dash_capstyle": "butt",
        }
    )

    fig, ax = plt.subplots(figsize=(9.5, 4.5))

    for mode in MODE_ORDER:
        subset = df[df["mode"] == mode].sort_values("progress_percent")
        if subset.empty:
            continue

        x = subset["x_cm"].to_numpy(dtype=float)
        y = subset["y_cm"].to_numpy(dtype=float)

        ax.plot(
            x,
            y,
            linewidth=LINE_WIDTH,
            label=mode,
            color=PURPLE,
            linestyle=LINE_STYLES[mode],
        )
        add_direction_arrows(ax, x, y, color=PURPLE)

        ax.scatter(x[0], y[0], marker="o", s=START_SIZE, color=PURPLE, edgecolor="0.35", linewidth=1.2, zorder=7)
        ax.scatter(x[-1], y[-1], marker="x", s=END_SIZE, color=PURPLE, linewidth=2.0, zorder=7)

    ax.scatter([], [], marker="o", s=START_SIZE, color=PURPLE, edgecolor="0.35", linewidth=1.2, label="Start")
    ax.scatter([], [], marker="x", s=END_SIZE, color=PURPLE, linewidth=2.0, label="End")
    ax.plot([], [], marker=">", markersize=9, color="0.25", linestyle="None", label="Direction")

    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")
    ax.set_xlim(-80, 190)
    ax.set_ylim(-20, 90)
    style_axis(ax)
    ax.legend(
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
        handlelength=2.2,
    )
    fig.subplots_adjust(left=0.10, right=0.62, bottom=0.18, top=0.95)
    return fig


if __name__ == "__main__":
    figure = plot_turn_paths(averaged_tracks())
    plt.show()
