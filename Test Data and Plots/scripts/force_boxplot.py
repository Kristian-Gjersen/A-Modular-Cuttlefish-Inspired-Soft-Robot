from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data" / "Force Test"

FIN_ORDER = ["Pink", "Purple", "Blue"]
DUTY_ORDER = [50, 75, 100]
FIN_COLORS = {
    "Pink": "#efa0c6",
    "Purple": "#b56ab4",
    "Blue": "#8fa4e8",
}

TRIAL_FORCE_VALUE = "mean"

LOAD_CELL_CAPACITY_LBF = 5.0
LBF_TO_N = 4.4482216152605
LOAD_CELL_CAPACITY_N = LOAD_CELL_CAPACITY_LBF * LBF_TO_N
ZERO_VOLTAGE = 0.0
FULL_SCALE_OUTPUT_V = 5.0
DISTANCE_TO_SENSOR = 5.0
DISTANCE_TO_ROBOT = 56.0


def voltage_to_force(voltage):
    return (
        (voltage - ZERO_VOLTAGE)
        / (FULL_SCALE_OUTPUT_V - ZERO_VOLTAGE)
        * LOAD_CELL_CAPACITY_N
        * (DISTANCE_TO_SENSOR / DISTANCE_TO_ROBOT)
    )


def parse_trial_name(path):
    match = re.match(r"^(Pink|Purple|Blue)_Fin_(50|75|100)_(\d+)\.csv$", path.name)
    if match is None:
        return None

    fin, duty, trial = match.groups()
    return fin, int(duty), int(trial)


def trial_force(values):
    values = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if values.size == 0:
        return None

    if TRIAL_FORCE_VALUE == "mean":
        return float(np.mean(values))
    if TRIAL_FORCE_VALUE == "max":
        return float(np.max(values))

    raise ValueError("TRIAL_FORCE_VALUE must be 'mean' or 'max'")


def load_trials(data_dir):
    rows = []

    for path in sorted(data_dir.glob("*.csv")):
        parsed = parse_trial_name(path)
        if parsed is None:
            continue

        columns = pd.read_csv(path, nrows=0).columns
        if "voltage" in columns:
            df = pd.read_csv(path, usecols=["voltage"])
            force_values = voltage_to_force(pd.to_numeric(df["voltage"], errors="coerce"))
        elif "force_N" in columns:
            df = pd.read_csv(path, usecols=["force_N"])
            force_values = df["force_N"]
        else:
            raise ValueError(f"No voltage or force_N column found in {path.name}")

        force = trial_force(force_values)
        if force is None:
            continue

        fin, duty, trial = parsed
        rows.append({"fin": fin, "duty": duty, "trial": trial, "force_N": force})

    if not rows:
        raise FileNotFoundError(f"No usable force CSV files found in {data_dir}")

    return pd.DataFrame(rows)


def plot_force_boxplot(data_dir):
    trials = load_trials(data_dir)
    boxplot_data = []
    boxplot_positions = []
    boxplot_colors = []

    group_spacing = 1.0
    total_width = 0.72
    box_spacing = total_width / len(FIN_ORDER)
    box_width = box_spacing * 0.72

    for duty_index, duty in enumerate(DUTY_ORDER):
        center = duty_index * group_spacing

        for fin_index, fin in enumerate(FIN_ORDER):
            values = trials[(trials["duty"] == duty) & (trials["fin"] == fin)]["force_N"].to_numpy(dtype=float)
            if values.size == 0:
                continue

            position = center - total_width / 2 + box_spacing / 2 + fin_index * box_spacing
            boxplot_data.append(values)
            boxplot_positions.append(position)
            boxplot_colors.append(FIN_COLORS[fin])

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "mathtext.fontset": "dejavuserif",
            "axes.labelsize": 22,
            "xtick.labelsize": 20,
            "ytick.labelsize": 20,
            "legend.fontsize": 18,
            "legend.title_fontsize": 20,
        }
    )

    fig, ax = plt.subplots(figsize=(10, 7))
    bp = ax.boxplot(
        boxplot_data,
        positions=boxplot_positions,
        widths=box_width,
        patch_artist=True,
        showmeans=False,
        showfliers=False,
        whis=1.5,
        manage_ticks=False,
        boxprops={"edgecolor": "0.35", "linewidth": 1.4, "alpha": 0.9},
        medianprops={"color": "black", "linewidth": 2.0},
        whiskerprops={"color": "black", "linewidth": 1.4},
        capprops={"color": "black", "linewidth": 1.4},
    )

    for patch, color in zip(bp["boxes"], boxplot_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
        patch.set_edgecolor("0.35")
        patch.set_linewidth(1.4)

    ax.set_xlabel("Duty cycle (%)", labelpad=12)
    ax.set_ylabel("Force (N)", labelpad=12)
    ax.set_xticks([i * group_spacing for i in range(len(DUTY_ORDER))])
    ax.set_xticklabels([str(duty) for duty in DUTY_ORDER])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.3)
    ax.spines["bottom"].set_linewidth(1.3)
    ax.tick_params(axis="both", width=1.2, length=6, pad=8)
    ax.grid(False)

    handles = [
        Patch(facecolor=FIN_COLORS[fin], edgecolor="0.35", label=fin, alpha=0.85)
        for fin in FIN_ORDER
    ]
    ax.legend(
        handles=handles,
        title="Fin Type",
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
    )

    fig.subplots_adjust(right=0.82)
    plt.show()


if __name__ == "__main__":
    plot_force_boxplot(DATA_DIR)