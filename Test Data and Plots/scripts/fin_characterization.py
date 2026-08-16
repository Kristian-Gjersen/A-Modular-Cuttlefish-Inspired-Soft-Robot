from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter


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

FIN = 2                 # Change this to Fin1, Fin2, etc.

COLORS = ["Pink", "Purple", "Blue"]
STATES = ["Wet", "Dry"]

PLOT_MULTIPLIER = 2     # 1 = one duty cycle, 2 = twice as much, 3 = three times as much
N_POINTS = 800
MIN_CYCLE_SECONDS = 8
CENTER_Y = False        # True = subtract mean Y from each curve

ALPHA = 0.02


MANUAL_WINDOW_SHIFT_PERCENT = {
    "Pink": 0,
    "Purple": -35,
    "Blue": 0,
}


VISUAL_DRY_X_SHIFT_PERCENT = {
    "Pink": 0,
    "Purple": -30,
    "Blue": 0,
}


STATE_LABELS = {
    "Wet": "Under Water",
    "Dry": "On Land",
}

STATE_LINESTYLES = {
    "Wet": "-",
    "Dry": "--",
}

PLOT_COLORS = {
    "Pink": "#efa0c6",
    "Purple": "#7374b6",
    "Blue": "#37a1d9",
}


# ----------------------------
# Functions
# ----------------------------

def read_fin_file(path):
    data = np.loadtxt(path, delimiter=",")
    time = data[:, 0]
    y = data[:, 1]
    return time, y


def find_one_duty_cycle(time, y):
    """
    Finds one duty cycle:
    one peak to the next peak.
    """

    dt = np.median(np.diff(time))

    smooth_seconds = 0.7
    window = int(round(smooth_seconds / dt))

    if window % 2 == 0:
        window += 1

    window = max(window, 5)

    if window >= len(y):
        window = len(y) - 1 if len(y) % 2 == 0 else len(y)

    y_smooth = savgol_filter(y, window, 3)

    min_distance = int(round(MIN_CYCLE_SECONDS / dt))
    prominence = 0.10 * np.ptp(y_smooth)

    peaks, _ = find_peaks(
        y_smooth,
        distance=min_distance,
        prominence=prominence
    )

    if len(peaks) < 2:
        raise ValueError("Could not find two peaks for one duty cycle.")

    middle_time = 0.5 * (time[0] + time[-1])

    peak_pairs = list(zip(peaks[:-1], peaks[1:]))

    best_pair = min(
        peak_pairs,
        key=lambda pair: abs(
            0.5 * (time[pair[0]] + time[pair[1]]) - middle_time
        )
    )

    start_time = time[best_pair[0]]
    end_time = time[best_pair[1]]

    return start_time, end_time


def fit_window_to_available_data(
    time,
    start_time,
    cycle_duration,
    x_min_percent,
    x_max_percent,
    label=""
):
    start_required = start_time + (x_min_percent / 100) * cycle_duration
    end_required = start_time + (x_max_percent / 100) * cycle_duration

    if end_required > time[-1]:
        amount = end_required - time[-1]
        start_time = start_time - amount
        start_required = start_required - amount
        end_required = end_required - amount

    if start_required < time[0]:
        amount = time[0] - start_required
        start_time = start_time + amount
        start_required = start_required + amount
        end_required = end_required + amount

    if start_required < time[0] or end_required > time[-1]:
        raise ValueError(
            "Not enough raw data to extract the requested curve.\n"
            f"Requested: {start_required:.2f}s to {end_required:.2f}s\n"
            f"Available:  {time[0]:.2f}s to {time[-1]:.2f}s"
        )

    return start_time


def alpha_filter(y, alpha=0.12):
    """
    Exponential smoothing / alpha filter.
    """

    y = np.asarray(y, dtype=float)

    y_filtered = np.empty_like(y)
    y_filtered[0] = y[0]

    for i in range(1, len(y)):
        y_filtered[i] = alpha * y[i] + (1 - alpha) * y_filtered[i - 1]

    return y_filtered


def get_cycle_info(state, color):
    """
    Reads the raw file and finds the detected one-cycle start/end.
    """

    filename = data_file(f"{color}_Fin_{state}_Fin{FIN}.csv")

    time, y = read_fin_file(filename)

    start, end = find_one_duty_cycle(time, y)
    cycle_duration = end - start

    return time, y, start, end, cycle_duration


def extract_processed_window(
    time,
    y,
    start_time,
    cycle_duration,
    label="",
    x_min_percent=0,
    x_max_percent=None
):
    """
    Extracts a processed curve from a chosen start time.

    x_min_percent and x_max_percent allow extra real data to be extracted
    before or after the normal 0–200% plotting range.
    """

    if x_max_percent is None:
        x_max_percent = PLOT_MULTIPLIER * 100

    start_time = fit_window_to_available_data(
        time=time,
        start_time=start_time,
        cycle_duration=cycle_duration,
        x_min_percent=x_min_percent,
        x_max_percent=x_max_percent,
        label=label
    )

    x_range = x_max_percent - x_min_percent
    n_points = int(round(N_POINTS * x_range / (PLOT_MULTIPLIER * 100)))
    n_points = max(n_points, 2)

    x_new = np.linspace(x_min_percent, x_max_percent, n_points)

    t_new = start_time + (x_new / 100) * cycle_duration

    y_new = np.interp(t_new, time, y)

    if CENTER_Y:
        y_new = y_new - np.mean(y_new)

    y_new = y_new * 100

    y_new = alpha_filter(y_new, alpha=ALPHA)

    return x_new, y_new


def find_phase_shift_percent(y_ref, y_target):
    """
    Finds the horizontal phase shift needed to align y_target to y_ref.
    """

    ref_centered = y_ref - np.mean(y_ref)
    target_centered = y_target - np.mean(y_target)

    correlation = np.correlate(target_centered, ref_centered, mode="full")
    shift_index = np.argmax(correlation) - (len(ref_centered) - 1)

    dx = (PLOT_MULTIPLIER * 100) / (len(y_ref) - 1)
    shift_percent = shift_index * dx

    return shift_percent


def vertically_align_to_reference(x_ref, y_ref, x_target_plot, y_target):
    """
    Vertically shifts y_target so it aligns with y_ref over the visible plot range.
    """

    y_target_on_ref = np.interp(
        x_ref,
        x_target_plot,
        y_target
    )

    vertical_offset = np.mean(y_ref) - np.mean(y_target_on_ref)

    y_target_aligned = y_target + vertical_offset

    return y_target_aligned


# ----------------------------
# Plotting style
# ----------------------------

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
    "mathtext.fontset": "dejavuserif",
    "axes.labelsize": 22,
    "axes.titlesize": 22,
    "xtick.labelsize": 20,
    "ytick.labelsize": 20,
    "legend.fontsize": 18,
    "legend.title_fontsize": 20,
})


# ----------------------------
# Plotting
# ----------------------------

fig, axes = plt.subplots(
    1,
    3,
    figsize=(18, 6),
    sharey=True
)


for ax, color in zip(axes, COLORS):
    ax.set_box_aspect(1)

    # ----------------------------
    # Get raw cycle information
    # ----------------------------

    wet_time, wet_y_raw, wet_start, wet_end, wet_cycle_duration = get_cycle_info(
        "Wet",
        color
    )

    dry_time, dry_y_raw, dry_start, dry_end, dry_cycle_duration = get_cycle_info(
        "Dry",
        color
    )

    # ----------------------------
    # Manual left/right shift of extraction window
    # ----------------------------

    window_shift_percent = MANUAL_WINDOW_SHIFT_PERCENT.get(color, 0)

    wet_start = wet_start + (window_shift_percent / 100) * wet_cycle_duration
    dry_start = dry_start + (window_shift_percent / 100) * dry_cycle_duration

    # ----------------------------
    # Extract Wet curve
    # ----------------------------

    x_wet, y_wet = extract_processed_window(
        wet_time,
        wet_y_raw,
        wet_start,
        wet_cycle_duration,
        label=f"{color} Wet"
    )

    # ----------------------------
    # Initial Dry extraction for phase alignment
    # ----------------------------

    x_dry_initial, y_dry_initial = extract_processed_window(
        dry_time,
        dry_y_raw,
        dry_start,
        dry_cycle_duration,
        label=f"{color} Dry initial"
    )

    # ----------------------------
    # Find Dry phase shift
    # ----------------------------

    dry_shift_percent = find_phase_shift_percent(
        y_wet,
        y_dry_initial
    )

    dry_shift_seconds = (dry_shift_percent / 100) * dry_cycle_duration
    dry_start_shifted = dry_start + dry_shift_seconds

    # ----------------------------
    # Extract extra real Dry data so visual shifting does not cut it off
    # ----------------------------

    dry_visual_shift = VISUAL_DRY_X_SHIFT_PERCENT.get(color, 0)

    dry_x_min = -dry_visual_shift
    dry_x_max = (PLOT_MULTIPLIER * 100) - dry_visual_shift

    x_dry, y_dry = extract_processed_window(
        dry_time,
        dry_y_raw,
        dry_start_shifted,
        dry_cycle_duration,
        label=f"{color} Dry final",
        x_min_percent=dry_x_min,
        x_max_percent=dry_x_max
    )

    x_dry_plot = x_dry + dry_visual_shift

    y_dry = vertically_align_to_reference(
        x_wet,
        y_wet,
        x_dry_plot,
        y_dry
    )

    # ----------------------------
    # Plot curves
    # ----------------------------

    ax.plot(
        x_wet,
        y_wet,
        label=STATE_LABELS["Wet"],
        color=PLOT_COLORS[color],
        linestyle=STATE_LINESTYLES["Wet"],
        linewidth=2.8,
        alpha=0.95,
    )

    ax.plot(
        x_dry_plot,
        y_dry,
        label=STATE_LABELS["Dry"],
        color=PLOT_COLORS[color],
        linestyle=STATE_LINESTYLES["Dry"],
        linewidth=2.8,
        alpha=0.95,
    )

    ax.set_title(f"{color} Fin", pad=12)
    ax.set_xlabel("Camshaft Rotation (%)", labelpad=12)

    ax.grid(False)

    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_linewidth(1.3)
    ax.spines["bottom"].set_linewidth(1.3)
    plt.yticks([-4, -2, 0, 2])

    ax.tick_params(
        axis="both",
        width=1.2,
        length=6,
        pad=8
    )

    ax.set_xlim(0, PLOT_MULTIPLIER * 100)
    ax.margins(y=0.08)


# ----------------------------
# Axis labels and y-axis numbers
# ----------------------------

axes[0].set_ylabel("Displacement (cm)", labelpad=12)

yticks = axes[0].get_yticks()
yticklabels = [f"{tick:g}" for tick in yticks]

for ax in axes:
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)

    ax.tick_params(
        axis="y",
        left=True,
        labelleft=True,
        width=1.2,
        length=6,
        pad=8
    )

    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_linewidth(1.3)


# ----------------------------
# Shared legend
# ----------------------------

handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    frameon=False,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.04),
    ncol=2,
)


fig.subplots_adjust(
    left=0.07,
    right=0.98,
    bottom=0.20,
    top=0.86,
    wspace=0.25,
)

plt.show()