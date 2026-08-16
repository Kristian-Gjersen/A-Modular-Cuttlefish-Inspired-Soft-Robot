from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ARCHIVE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ARCHIVE_ROOT / "CSV data" / "Speed Tests"

FIN_ORDER = ["Pink", "Purple", "Blue"]
DUTY_ORDER = [50, 75, 100]
FIN_COLORS = {
    "Pink": "#efa0c6",
    "Purple": "#7374b6",
    "Blue": "#37a1d9",
}

VALUE_COLUMNS = ["v_{x}_median", "vx_median", "y_downsampled"]
UNCERTAINTY_MODE = "std"
CONVERT_TO_CM_PER_S = True
USE_ABSOLUTE_VELOCITY = True


def parse_trial_name(path):
    parts = path.stem.split("_")
    if len(parts) < 4:
        return None

    fin = parts[0].title()
    duty = int(parts[2])
    trial = int(parts[3])
    return fin, duty, trial


def clean_fin_name(value):
    value = str(value).strip().lower()
    if "pink" in value:
        return "Pink"
    if "purple" in value:
        return "Purple"
    if "blue" in value:
        return "Blue"
    return value.title()


def load_trials(data_dir):
    rows = []

    for path in sorted(data_dir.glob("*.csv")):
        parsed = parse_trial_name(path)
        if parsed is None:
            continue

        file_fin, file_duty, file_trial = parsed
        df = pd.read_csv(path)
        value_column = next((col for col in VALUE_COLUMNS if col in df.columns), None)
        if value_column is None:
            raise ValueError(f"No velocity column found in {path.name}")

        fin = clean_fin_name(df["fin"].iloc[0]) if "fin" in df.columns else file_fin
        duty = int(df["speed"].iloc[0]) if "speed" in df.columns else file_duty
        trial = int(df["trial"].iloc[0]) if "trial" in df.columns else file_trial

        values = pd.to_numeric(df[value_column], errors="coerce").dropna()
        if values.empty:
            continue

        if USE_ABSOLUTE_VELOCITY:
            values = values.abs()

        rows.append(
            {
                "fin": fin,
                "duty": duty,
                "trial": trial,
                "velocity": float(values.mean()),
            }
        )

    if not rows:
        raise FileNotFoundError(f"No usable speed CSV files found in {data_dir}")

    return pd.DataFrame(rows)


def summarize_trials(trials):
    stats = (
        trials.groupby(["duty", "fin"], as_index=False)
        .agg(mean_value=("velocity", "mean"), std_value=("velocity", "std"), n=("velocity", "count"))
    )
    stats["sem_value"] = stats["std_value"] / np.sqrt(stats["n"])
    stats["ci95_value"] = 1.96 * stats["sem_value"]

    if UNCERTAINTY_MODE == "std":
        stats["uncertainty"] = stats["std_value"]
        label = "SD"
    elif UNCERTAINTY_MODE == "sem":
        stats["uncertainty"] = stats["sem_value"]
        label = "SEM"
    elif UNCERTAINTY_MODE == "ci95":
        stats["uncertainty"] = stats["ci95_value"]
        label = "95% CI"
    else:
        raise ValueError("UNCERTAINTY_MODE must be 'std', 'sem', or 'ci95'")

    return stats, label


def r_values(stats):
    rows = []
    for fin in FIN_ORDER:
        subset = stats[stats["fin"] == fin].sort_values("duty")
        if len(subset) < 2:
            continue

        x = subset["duty"].to_numpy(dtype=float)
        y = subset["mean_value"].to_numpy(dtype=float)
        if CONVERT_TO_CM_PER_S:
            y = y * 100

        rows.append((fin, np.corrcoef(x, y)[0, 1]))

    return rows


def plot_speed_pillar(data_dir):
    trials = load_trials(data_dir)
    stats, uncertainty_label = summarize_trials(trials)

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

    x = np.arange(len(DUTY_ORDER))
    bar_width = 0.16
    fig, ax = plt.subplots(figsize=(10, 7))

    for index, fin in enumerate(FIN_ORDER):
        subset = stats[stats["fin"] == fin].set_index("duty").reindex(DUTY_ORDER)
        values = subset["mean_value"].to_numpy(dtype=float)
        errors = subset["uncertainty"].to_numpy(dtype=float)

        if CONVERT_TO_CM_PER_S:
            values = values * 100
            errors = errors * 100

        offset = (index - (len(FIN_ORDER) - 1) / 2) * bar_width
        ax.bar(
            x + offset,
            values,
            width=bar_width,
            label=fin,
            color=FIN_COLORS[fin],
            edgecolor="0.35",
            linewidth=1.4,
            alpha=0.9,
            yerr=np.nan_to_num(errors, nan=0.0),
            capsize=5,
            error_kw={"elinewidth": 1.4, "capthick": 1.4, "ecolor": "0.25"},
        )

    ax.set_xlabel("Duty cycle (%)", labelpad=12)
    ax.set_ylabel("Velocity (cm/s)", labelpad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([str(duty) for duty in DUTY_ORDER])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.3)
    ax.spines["bottom"].set_linewidth(1.3)
    ax.tick_params(axis="both", width=1.2, length=6, pad=8)

    ax.legend(
        title=f"Fin\nerror = {uncertainty_label}",
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0,
    )

    lines = ["Linear fit:"]
    lines.extend(f"{fin}: R = {r:.3f}" for fin, r in r_values(stats))
    ax.text(1.02, 0.58, "\n".join(lines), transform=ax.transAxes, fontsize=16, va="top", ha="left")

    fig.subplots_adjust(right=0.82)
    plt.show()


if __name__ == "__main__":
    plot_speed_pillar(DATA_DIR)