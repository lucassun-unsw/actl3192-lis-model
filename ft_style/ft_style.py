"""FT-style figure helpers (FINS3645 lecturer style)."""

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, NullFormatter

FT_CREAM = "#FDF1E6"
FT_MAROON = "#990F3D"
FT_BLUE = "#0F5499"
FT_TEAL = "#2F7F73"
FT_TAN = "#9C8B7A"
FT_AXIS = "#66605C"
FT_GRID = "#E2D8CF"
FT_TITLE = "#262A33"
FT_GREY = "#6B625C"


def apply_ft_style():
    """Set rcParams so the next figure follows the FT look."""
    plt.rcParams.update({
        "figure.facecolor": FT_CREAM, "axes.facecolor": FT_CREAM,
        "savefig.facecolor": FT_CREAM,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.edgecolor": FT_AXIS, "axes.grid": True, "grid.color": FT_GRID,
        "axes.axisbelow": True, "font.family": "DejaVu Sans", "font.size": 12,
        "axes.formatter.useoffset": False,
    })


def ft_header(fig, title, subtitle, source, right=0.86):
    """Bold title, grey subtitle, and bottom-left source note.

    `right` leaves room for direct end labels; use 0.95 if there are none.
    """
    fig.text(0.012, 0.96, title, fontsize=15, fontweight="bold", color=FT_TITLE)
    fig.text(0.012, 0.91, subtitle, fontsize=11, color=FT_GREY)
    fig.text(0.012, 0.01, source, fontsize=8, color=FT_GREY)
    fig.subplots_adjust(top=0.86, bottom=0.10, right=right)


def day_boundary_ticks(index: pd.DatetimeIndex):
    """Tick positions/labels at the first bar of each trading day.

    Plot intraday data on a sequential index (0, 1, 2, ...) so nights and
    weekends never render as diagonal jumps.
    """
    positions, labels, last_day = [], [], None
    for i, ts in enumerate(index):
        if ts.date() != last_day:
            positions.append(i)
            labels.append(ts.strftime("%d %b"))
            last_day = ts.date()
    return positions, labels


def dollar_log_axis(ax, ticks=(1, 2, 5, 10, 20, 50, 100)):
    """Log y-axis with plain $ labels instead of 10^0, 10^1, ..."""
    ax.set_yscale("log")
    ax.set_yticks(list(ticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.yaxis.set_minor_formatter(NullFormatter())


def save(fig, path):
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    # Quick demo: python ft_style.py -> writes ft_style_demo.png
    import numpy as np

    dates = pd.date_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(0)
    a = pd.Series(np.exp(np.cumsum(rng.normal(0.003, 0.03, 500))), index=dates)
    b = pd.Series(np.exp(np.cumsum(rng.normal(0.0005, 0.01, 500))), index=dates)

    apply_ft_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(a.index, a, color=FT_MAROON, linewidth=2.4)
    ax.plot(b.index, b, color=FT_BLUE, linewidth=1.6)
    ax.axhline(1.0, color=FT_AXIS, linewidth=0.8)
    ax.set_ylabel("US dollars")
    for s, c, name in [(a, FT_MAROON, "Asset A"), (b, FT_BLUE, "Asset B")]:
        ax.annotate(f"  {name} ${s.iloc[-1]:.2f}", xy=(s.index[-1], s.iloc[-1]),
                    color=c, fontweight="bold", va="center")
    ft_header(fig, "Asset A grew faster than Asset B",
              "Growth of $1, simulated daily data, 500 trading days",
              "Source: simulated data | demo only")
    save(fig, "ft_style_demo.png")
    print("Saved ft_style_demo.png")
