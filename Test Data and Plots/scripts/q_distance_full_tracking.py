from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data"

FOLDERS = ["Min", "Mid", "Max"]
FILE_STEM = "Fin1"

CONVERT_TO_CM = True
ALPHA = 0.4

FIG_WIDTH_IN = 6.8
FIG_HEIGHT_IN = 3.2
LINE_WIDTH = 1.6

PLOT_COLORS = {
    "Min": "#ff0000",
    "Mid": "#ff861a",
    "Max": "#37a537",
}


def data_file(name):
    matches = sorted(DATA_DIR.rglob(name))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise FileNotFoundError(f"Multiple data files named {name!r}: {matches}")
    raise FileNotFoundError(f"Could not find {name!r} under {DATA_DIR}")


def alpha_filter(y, alpha):
    y = np.asarray(y, dtype=float)
    filtered = np.empty_like(y)
    filtered[0] = y[0]

    for index in range(1, len(y)):
        filtered[index] = alpha * y[index] + (1 - alpha) * filtered[index - 1]

    return filtered


def load_raw_data():
    raw_data = {}

    for folder in FOLDERS:
        path = data_file(f"{folder}_Full_Tracking_{FILE_STEM}.csv")
        data = np.loadtxt(path, delimiter=",")
        time = data[:, 0]
        displacement = data[:, 1]

        if CONVERT_TO_CM:
            displacement = displacement * 100

        raw_data[folder] = (time, displacement)

    return raw_data


def apply_plot_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "mathtext.fontset": "dejavuserif",
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
        }
    )


def style_axes(ax):
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
    ax.tick_params(axis="both", width=0.8, length=3, pad=2)


def plot_raw_tracking(raw_data):
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))

    for folder in FOLDERS:
        time, displacement = raw_data[folder]
        displacement = alpha_filter(displacement, ALPHA)

        ax.plot(
            time,
            displacement,
            label=folder,
            color=PLOT_COLORS[folder],
            linewidth=LINE_WIDTH,
            alpha=0.95,
        )
        ax.axvline(time[0], color=PLOT_COLORS[folder], linewidth=1.0, alpha=0.35, linestyle="--")

    ax.set_title("Full raw tracking file")
    ax.set_xlabel("Original tracking time (s)", labelpad=4)
    ax.set_ylabel("Displacement (cm)" if CONVERT_TO_CM else "Y position (m)", labelpad=4)
    style_axes(ax)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    apply_plot_style()
    plot_raw_tracking(load_raw_data())