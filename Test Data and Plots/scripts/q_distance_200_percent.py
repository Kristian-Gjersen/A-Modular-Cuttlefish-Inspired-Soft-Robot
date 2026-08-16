from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


# ----------------------------
# Settings
# ----------------------------

ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data"


def data_file(name):
    direct_path = DATA_DIR / name
    if direct_path.exists():
        return direct_path

    matches = sorted(DATA_DIR.rglob(name))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise FileNotFoundError(
            f"Multiple data files named {name!r} were found: {matches}"
        )

    raise FileNotFoundError(f"Could not find data file named {name!r} under {DATA_DIR}")

FOLDERS = ["Min", "Mid", "Max"]
FILE_NAME = "Fin1.txt"

START_TIMES = {
    "Min": 2.085789E0,
    "Mid": 2.906689E0,
    "Max": 2.739156E0,
}

TRIM_END_SECONDS = 1.0

PLOT_DURATION = 3

X_AXIS_PERCENT_END = 200

CONVERT_TO_CM = True

ALPHA = 0.4


# ----------------------------
# Figure size in points
# ----------------------------

FIG_WIDTH_PT = 259.8699
FIG_HEIGHT_PT = 118.3398

PT_PER_INCH = 72.27
FIG_WIDTH_IN = FIG_WIDTH_PT / PT_PER_INCH
FIG_HEIGHT_IN = FIG_HEIGHT_PT / PT_PER_INCH


PLOT_COLORS = {
    "Min": "#ff0000",
    "Mid": "#ff861a",
    "Max": "#37a537",
}

LINE_WIDTH = 1.6


def alpha_filter(y, alpha=0.12):
    """
    Exponential smoothing / alpha filter.

    Smaller alpha = smoother curve, but more delay.
    Larger alpha = follows the raw data more closely.
    Typical values: 0.05 to 0.25
    """
    y = np.asarray(y, dtype=float)

    y_filtered = np.empty_like(y)
    y_filtered[0] = y[0]

    for i in range(1, len(y)):
        y_filtered[i] = alpha * y[i] + (1 - alpha) * y_filtered[i - 1]

    return y_filtered


# ----------------------------
# Load and align data first
# ----------------------------

aligned_data = {}
end_times = []

for folder in FOLDERS:
    file_path = data_file(f"{folder}_Short_Test_{Path(FILE_NAME).stem}.csv")

    data = np.loadtxt(file_path, delimiter=",")

    time = data[:, 0]
    y_position = data[:, 1]

    start_time = START_TIMES[folder]

    aligned_time = time - start_time

    mask = aligned_time >= 0
    aligned_time = aligned_time[mask]
    y_position = y_position[mask]

    if CONVERT_TO_CM:
        y_position = y_position * 100

    aligned_data[folder] = (aligned_time, y_position)
    end_times.append(aligned_time[-1])


# ----------------------------
# Find common end time
# ----------------------------

if PLOT_DURATION is None:
    common_end_time = min(end_times) - TRIM_END_SECONDS
else:
    common_end_time = PLOT_DURATION

if common_end_time <= 0:
    raise ValueError("Common end time is too small. Reduce TRIM_END_SECONDS.")


# ----------------------------
# Plotting style
# ----------------------------

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
    "mathtext.fontset": "dejavuserif",
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.title_fontsize": 8,
})


# ----------------------------
# Plotting
# ----------------------------

fig, ax = plt.subplots(figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))

for folder in FOLDERS:
    aligned_time, y_position = aligned_data[folder]

    mask = aligned_time <= common_end_time
    aligned_time = aligned_time[mask]
    y_position = y_position[mask]

    y_position = alpha_filter(y_position, alpha=ALPHA)

    x_percent = (aligned_time / common_end_time) * X_AXIS_PERCENT_END

    ax.plot(
        x_percent,
        y_position,
        label=folder,
        color=PLOT_COLORS.get(folder),
        linewidth=LINE_WIDTH,
        alpha=0.95,
    )


# ----------------------------
# Axis labels
# ----------------------------

ax.set_xlabel("Camshaft Rotation (%)", labelpad=4)

if CONVERT_TO_CM:
    ax.set_ylabel("Displacement (cm)", labelpad=4)
else:
    ax.set_ylabel("Y position (m)", labelpad=4)


# ----------------------------
# Axis style
# ----------------------------

ax.grid(False)

ax.spines["top"].set_visible(True)
ax.spines["right"].set_visible(True)
ax.spines["left"].set_visible(True)
ax.spines["bottom"].set_visible(True)

for spine in ax.spines.values():
    spine.set_linewidth(0.8)

ax.tick_params(axis="both", width=0.8, length=3, pad=2)

ax.set_xlim(0, X_AXIS_PERCENT_END)
ax.set_xticks(np.arange(0, X_AXIS_PERCENT_END + 1, 50))

ax.set_ylim(-5, 3)
plt.yticks([-4, -2, 0, 2])


# ----------------------------
# Legend
# ----------------------------

ax.legend(
    frameon=False,
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
    borderaxespad=0,
)


# ----------------------------
# Layout
# ----------------------------

fig.subplots_adjust(
    left=0.18,
    right=0.76,
    bottom=0.28,
    top=0.96,
)

plt.show()