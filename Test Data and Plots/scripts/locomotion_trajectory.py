from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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

file_path = data_file("locomotion_trajectory_tracking_used_for_plot.csv")

# -------------------------
# Settings
# -------------------------

ALPHA = 0.06
APPLY_ALPHA_FILTER = True

LINE_WIDTH = 2.8

M_TO_CM = 100            # Convert plotted coordinates from meters to centimeters

ARROW_COUNT = 4          # Number of direction arrows per plotted path
ARROW_SIZE = 30          # Arrowhead size
ARROW_WIDTH = 1.8        # Arrow line width

PLOT_COLORS = {
    "forward": "#7374b6",
    "back": "#6d009a",
    #"trajectory": "#89a2e5",
    "start": "#7374b6",
    "end": "#6d009a",
}


# -------------------------
# Functions
# -------------------------

def alpha_filter(values, alpha=0.02):
    """
    Exponential smoothing / alpha filter.

    Smaller alpha = smoother curve, but more delay.
    Larger alpha = follows the raw data more closely.
    """
    values = np.asarray(values, dtype=float)

    filtered = np.empty_like(values)
    filtered[0] = values[0]

    for i in range(1, len(values)):
        filtered[i] = alpha * values[i] + (1 - alpha) * filtered[i - 1]

    return filtered


def style_axis(ax):
    """Apply a closed-box plot style."""

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.3)

    ax.tick_params(axis="both", width=1.2, length=6, pad=8)

    ax.set_aspect("equal", adjustable="box")


def add_direction_arrows(ax, x, y, n_arrows=3, color="black"):
    """Add arrows along a trajectory to show movement direction."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        return

    arrow_indices = np.linspace(0, len(x) - 2, n_arrows + 2, dtype=int)[1:-1]

    for i in arrow_indices:
        j = i + 1

        if x[i] == x[j] and y[i] == y[j]:
            continue

        ax.annotate(
            "",
            xy=(x[j], y[j]),
            xytext=(x[i], y[i]),
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


# -------------------------
# Plot style
# -------------------------

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
    "mathtext.fontset": "dejavuserif",
    "axes.labelsize": 22,
    "xtick.labelsize": 20,
    "ytick.labelsize": 20,
    "legend.fontsize": 18,
    "legend.title_fontsize": 20,
})


# -------------------------
# Read and clean data
# -------------------------

df = pd.read_csv(file_path, skiprows=1)

df["x"] = pd.to_numeric(df["x"], errors="coerce")
df["y"] = pd.to_numeric(df["y"], errors="coerce")
df = df.dropna(subset=["x", "y"]).reset_index(drop=True)

if APPLY_ALPHA_FILTER:
    df["x_plot"] = alpha_filter(df["x"], alpha=ALPHA)
    df["y_plot"] = alpha_filter(df["y"], alpha=ALPHA)
else:
    df["x_plot"] = df["x"]
    df["y_plot"] = df["y"]

df["x_plot"] = df["x_plot"] * M_TO_CM
df["y_plot"] = df["y_plot"] * M_TO_CM


turn_idx = df["x_plot"].idxmax()

half_idx = len(df) // 2
df_first_half = df.iloc[:half_idx + 1]


# -------------------------
# Plot 1: Full trajectory
# -------------------------

fig, ax = plt.subplots(figsize=(8, 8))

line_forward, = ax.plot(
    df.loc[:turn_idx, "x_plot"],
    df.loc[:turn_idx, "y_plot"],
    linewidth=LINE_WIDTH,
    label="Path Forward",
    color=PLOT_COLORS["forward"],
    alpha=0.95,
)

add_direction_arrows(
    ax,
    df.loc[:turn_idx, "x_plot"],
    df.loc[:turn_idx, "y_plot"],
    n_arrows=ARROW_COUNT,
    color=line_forward.get_color(),
)

# Path back
line_back, = ax.plot(
    df.loc[turn_idx:, "x_plot"],
    df.loc[turn_idx:, "y_plot"],
    linewidth=LINE_WIDTH,
    label="Path Back",
    color=PLOT_COLORS["back"],
    alpha=0.95,
)

add_direction_arrows(
    ax,
    df.loc[turn_idx:, "x_plot"],
    df.loc[turn_idx:, "y_plot"],
    n_arrows=ARROW_COUNT,
    color=line_back.get_color(),
)

ax.scatter(
    df["x_plot"].iloc[0],
    df["y_plot"].iloc[0],
    marker="o",
    s=80,
    label="Start",
    color=PLOT_COLORS["start"],
    edgecolor="0.35",
    linewidth=1.2,
    zorder=5,
)

ax.scatter(
    df["x_plot"].iloc[-1],
    df["y_plot"].iloc[-1],
    marker="x",
    s=90,
    label="End",
    color=PLOT_COLORS["end"],
    linewidth=2.0,
    zorder=5,
)

ax.set_xlabel("x (cm)", labelpad=12)
ax.set_ylabel("y (cm)", labelpad=12)

ax.set_xlim(0, 215)
ax.set_ylim(-50, 50)
ax.set_yticks([-50, 0, 50])

style_axis(ax)

ax.legend(
    frameon=False,
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
    borderaxespad=0,
)

fig.subplots_adjust(right=0.78)

plt.show()
