# FT-Style Graph Guide (FINS3645 lecturer style)

A self-contained spec for the beige Financial Times (FT) figure style used in the
FINS3645 lecture decks. Drop this file into any project and tell the AI:
"Make every figure follow `ft_style_graph.md`."

Source of truth in the fins-agent repo:
`fins2026/week4/scratch/dff_walkthrough/dff_helpers.py` (style helpers),
`fins2026/week4/scratch/spacex_ipo/spacex_ipo.py` (intraday time series),
`fins2026/week5/scratch/crypto_vs_stocks/crypto_stock_figures.py` (log-scale axes).

---

## 1. The look at a glance

| Element | Setting |
|---|---|
| Background (figure + axes) | beige `#FDF1E6` |
| Spines | bottom only (top, right, and left off), colour `#66605C` |
| Grid | on, colour `#E2D8CF`, drawn below the data |
| Font | DejaVu Sans, size 12 |
| Figure size | `(10, 6)` default; `(10, 7)` or `(9, 8)` for dense plots |
| Export | PNG, `dpi=150` |
| Title | bold, 15 pt, `#262A33`, top-left, written with `fig.text` (not `ax.set_title`) |
| Subtitle | 11 pt, grey `#6B625C`, under the title |
| Source note | 8 pt, grey `#6B625C`, bottom-left: `Source: <source> \| <detail>` |
| Labels | direct labels on lines/bars instead of a legend where possible |

**The title states the conclusion**, not the topic.
Good: "Bitcoin returned 57x while the S&P 500 returned 4x".
Bad: "Bitcoin vs S&P 500 cumulative returns".

## 2. Palette

| Name | Hex | Use |
|---|---|---|
| `FT_CREAM` | `#FDF1E6` | background |
| `FT_MAROON` | `#990F3D` | primary series (the main subject) |
| `FT_BLUE` | `#0F5499` | secondary series, up bars, reference/offer lines |
| `FT_TEAL` | `#2F7F73` | third series (green `#276749` also acceptable) |
| `FT_TAN` | `#9C8B7A` | muted / context series |
| `FT_AXIS` | `#66605C` | axis spine, zero line, reference line |
| `FT_GRID` | `#E2D8CF` | gridlines |
| `FT_TITLE` | `#262A33` | title text |
| `FT_GREY` | `#6B625C` | subtitle and source text |

## 3. Copy-paste helper module (`ft_style.py`)

```python
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
```

## 4. Example: growth of $1, two series

```python
from ft_style import *

apply_ft_style()
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(btc.index, btc, color=FT_MAROON, linewidth=2.4)
ax.plot(spx.index, spx, color=FT_BLUE, linewidth=1.6)
ax.axhline(1.0, color=FT_AXIS, linewidth=0.8)
dollar_log_axis(ax)                 # log only because one series dwarfs the other
ax.set_ylabel("US dollars")

# Direct end labels instead of a legend
ax.annotate(f"  Bitcoin ${btc.iloc[-1]:,.0f}", xy=(btc.index[-1], btc.iloc[-1]),
            color=FT_MAROON, fontweight="bold", va="center")
ax.annotate(f"  S&P 500 ${spx.iloc[-1]:,.0f}", xy=(spx.index[-1], spx.iloc[-1]),
            color=FT_BLUE, fontweight="bold", va="center")

ft_header(fig,
          "Bitcoin turned $1 into $57; the S&P 500 turned it into $4",
          "Growth of $1 invested, daily, Jan 2015 to Dec 2025, log scale",
          "Source: Yahoo Finance | daily close prices, dividends not reinvested")
save(fig, "output/fig1_growth_of_1.png")
```

## 5. Example: intraday series without overnight gaps

```python
apply_ft_style()
fig, ax = plt.subplots(figsize=(10, 6))
n = range(len(prices))
ax.plot(n, prices.values, color=FT_MAROON, linewidth=2.4)

ticks, labels = day_boundary_ticks(prices.index)
ax.set_xticks(ticks)
ax.set_xticklabels(labels)
ax.grid(axis="x", visible=False)     # keep only horizontal gridlines
ax.annotate(f"  ${prices.iloc[-1]:.2f}", xy=(len(prices) - 1, prices.iloc[-1]),
            color=FT_MAROON, fontweight="bold", va="center")
ft_header(fig, "<conclusion>", "<what, frequency, period>", "Source: <source> | <detail>")
save(fig, "output/fig2_intraday.png")
```

If the first tick (position 0) collides with the next day's tick, drop it:
`ticks, labels = ticks[1:], labels[1:]`.

## 6. Rules checklist

1. Call `apply_ft_style()` **before** `plt.subplots(...)`.
2. Use `ft_header(...)` for title, subtitle, and source. Never `ax.set_title`.
3. Title = the finding. Subtitle = what is plotted, units, frequency, sample period.
4. Source note format: `Source: <provider> | <detail>`.
5. Maroon is the main subject; blue is the comparison; teal/tan for extras.
6. Prefer direct labels (`ax.annotate` at the last point) over a legend.
   Use a legend only when direct labels would overlap.
7. No scientific notation and no `10^n` ticks. On log axes use fixed round
   ticks with `$` labels (`dollar_log_axis`).
8. Use a log scale only when one series dwarfs the other; otherwise linear,
   with a "US dollars" y-label for growth of $1.
9. Intraday or trading-day data: plot on a sequential index with
   `day_boundary_ticks`, and hide vertical gridlines.
10. Horizontal bar charts with negative values: place value labels by sign
    (left-aligned for positive, right-aligned for negative, with a small pad)
    so they do not collide with the y-axis.
11. Add a thin `#66605C` reference line at 0 (returns) or 1 (growth of $1).
12. Direct end labels need right-side room: `ft_header(..., right=0.86)` (default).
13. Save at `dpi=150` and close the figure after saving.
