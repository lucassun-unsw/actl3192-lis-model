"""Report figures, following ft_style/ft_style_graph.md.

Departures from the style guide required by the brief: saved at params.chart_dpi
(300 dpi, not 150), and every series is also told apart by hatching, line style or
marker so the charts read in black and white.
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from .params import ROOT, Params  # noqa: E402

sys.path.insert(0, str(ROOT / "ft_style"))
from ft_style import (FT_AXIS, FT_BLUE, FT_CREAM, FT_GREY, FT_MAROON, FT_TAN, FT_TEAL,  # noqa: E402
                      apply_ft_style, ft_header)

SOURCE = ("Source: Group 23 LIS model | ABS Life Tables 2022-24 (females), Services Australia "
          "rates from 20 Sep 2026, judgement assumptions in params.py")

# Scenario look: colour, hatch (bars), line style and marker (lines)
STYLE = {
    "all_abp": dict(color=FT_TAN, hatch="", ls="--", marker="s", label="All ABP"),
    "current_lis": dict(color=FT_MAROON, hatch="", ls="-", marker="o", label="Current settings"),
    "retargeted": dict(color=FT_BLUE, hatch="///", ls="-.", marker="^", label="Retargeted"),
    "bonus": dict(color=FT_TEAL, hatch="...", ls=":", marker="D", label="Bonus (equal support)"),
    "bonus_flat": dict(color=FT_TAN, hatch="xxx", ls="--", marker="v", label="Flat bonus (upper bound)"),
}
HATCHES = ["", "///", "...", "xxx"]
SHADES = [FT_MAROON, FT_BLUE, FT_TEAL, FT_TAN]

dollars = FuncFormatter(lambda v, _: f"-${-v / 1000:,.0f}k" if v < 0 else f"${v / 1000:,.0f}k")


def _k(v):
    """$ thousands label, sign aware."""
    return f"-${-v / 1000:,.0f}k" if v < 0 else f"${v / 1000:,.0f}k"


def _d(v):
    """Whole dollars, sign aware."""
    return f"-${-v:,.0f}" if v < 0 else f"${v:,.0f}"


def _bal_label(b):
    return f"${b / 1_000_000:g}m" if b >= 1_000_000 else f"${b / 1000:,.0f}k"


def _style():
    """FT look, with mathtext off so "$" signs print as dollars."""
    apply_ft_style()
    plt.rcParams["text.parse_math"] = False


def _save(fig, path, p: Params):
    fig.savefig(path, dpi=p.chart_dpi)
    plt.close(fig)


def _grouped_bars(ax, x_labels, series, width=0.8):
    """series: list of (values, colour, hatch, label). Returns bar containers."""
    n = len(series)
    w = width / n
    x = np.arange(len(x_labels))
    bars = []
    for i, (vals, color, hatch, label) in enumerate(series):
        bars.append(ax.bar(x - width / 2 + w * (i + 0.5), vals, w, color=color, hatch=hatch,
                           edgecolor="white" if not hatch else "black", linewidth=0.6, label=label))
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.axhline(0, color=FT_AXIS, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(dollars)
    return bars, x, w


def _label_bars(ax, bars, fontsize=8):
    """Value labels above positive bars and below negative bars."""
    for container in bars:
        for rect in container:
            h = rect.get_height()
            ax.annotate(_k(h), (rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3 if h >= 0 else -3), textcoords="offset points",
                        ha="center", va="bottom" if h >= 0 else "top", fontsize=fontsize, color=FT_GREY)


def chart_pv_age_pension(results, p: Params, path):
    """1. Change in PV Age Pension by balance: current vs retargeted vs bonus."""
    scens = ["current_lis", "retargeted", "bonus"]
    bals = list(p.balances)
    piv = results.pivot(index="balance", columns="scenario", values="d_pv_age_pension").loc[bals]
    gov = results.pivot(index="balance", columns="scenario", values="gov_cost").loc[bals]

    _style()
    fig, ax = plt.subplots(figsize=(10, 6))
    series = [(piv[s].to_numpy(), STYLE[s]["color"], STYLE[s]["hatch"], STYLE[s]["label"]) for s in scens]
    bars, x, w = _grouped_bars(ax, [_bal_label(b) for b in bals], series)
    _label_bars(ax, bars[:2])
    for rect, g in zip(bars[2], gov["bonus"].to_numpy()):
        h = rect.get_height()
        y = max(h, g) if h >= 0 else min(h, g)
        ax.annotate(_k(h), (rect.get_x() + rect.get_width() / 2, y), xytext=(0, 7 if h >= 0 else -7),
                    textcoords="offset points", ha="center", va="bottom" if h >= 0 else "top",
                    fontsize=8, color=FT_GREY)
    ax.scatter(x + w, gov["bonus"].to_numpy(), marker="D", s=40, color="black", zorder=5,
               label="Bonus incl. bonus payment (total cost)")
    ax.set_ylabel("Change in PV of Age Pension vs all ABP")
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    coh = [b for b in bals if b in p.cohort_balances]
    hi = [b for b in bals if b not in p.cohort_balances]
    d_coh = (piv.loc[coh, "retargeted"] - piv.loc[coh, "current_lis"]).mean()
    d_hi = (piv.loc[hi, "retargeted"] - piv.loc[hi, "current_lis"]).mean()
    title = (f"Retargeting: {'+' if d_coh > 0 else '-'}{_k(abs(d_coh))} per cohort member, "
             f"{'+' if d_hi > 0 else '-'}{_k(abs(d_hi))} per higher balance member")
    ft_header(fig, title,
              f"Change in PV of Age Pension vs all ABP, today's dollars, {p.lis_allocation:.0%} in a LIS at 67, "
              f"cap {_k(p.cap)}, {p.inc_pct_in:.0%} income test inside cap",
              SOURCE, right=0.97)
    _save(fig, path, p)


def chart_ap_by_age(proj, p: Params, path):
    """2. Age Pension by age for the chart member: all ABP vs current LIS vs retargeted."""
    scens = ["all_abp", "current_lis", "retargeted"]
    bal = p.chart_member
    _style()
    fig, ax = plt.subplots(figsize=(10, 6))
    ends = []
    for s in scens:
        df = proj[(s, bal)]
        st = STYLE[s]
        ax.plot(df["age"], df["age_pension"], color=st["color"], ls=st["ls"], marker=st["marker"],
                markevery=5, linewidth=2.4 if s == "current_lis" else 1.8)
        ends.append([df["age"].iloc[-1], df["age_pension"].iloc[-1], st])
    # spread end labels so they do not overlap
    ends.sort(key=lambda e: e[1])
    gap = 0.04 * (ax.get_ylim()[1] - ax.get_ylim()[0])
    for i in range(1, len(ends)):
        ends[i][1] = max(ends[i][1], ends[i - 1][1] + gap)
    for age, y, st in ends:
        ax.annotate(f"  {st['label']}", xy=(age, y), color=st["color"], fontweight="bold", va="center", fontsize=10)
    ax.hlines(p.max_rate, p.retirement_age, p.max_age, color=FT_AXIS, linewidth=0.8, ls=":")
    ax.annotate("Maximum rate", xy=(p.retirement_age, p.max_rate), xytext=(0, 4), textcoords="offset points",
                fontsize=9, color=FT_GREY)
    ax.set_xlabel("Age")
    ax.set_ylabel("Age Pension a year")
    ax.yaxis.set_major_formatter(dollars)

    pv = {s: (proj[(s, bal)]["tpx"] * proj[(s, bal)]["discount"] * proj[(s, bal)]["age_pension"]).sum()
          for s in scens}
    title = (f"A LIS adds {_k(pv['current_lis'] - pv['all_abp'])} of PV Age Pension for a {_bal_label(bal)} "
             f"retiree now, {_k(pv['retargeted'] - pv['all_abp'])} if retargeted")
    ft_header(fig, title,
              f"Age Pension by age if alive, {_bal_label(bal)} single female homeowner, today's dollars, "
              f"{p.lis_allocation:.0%} in a LIS at 67", SOURCE)
    fig.subplots_adjust(bottom=0.12)
    _save(fig, path, p)


def chart_age_of_death(aod, p: Params, path, scenario="current_lis"):
    """3. Gains and losses by age of death for each balance: extra income and change in bequest."""
    a = aod[aod["scenario"] == scenario]
    bals = list(p.balances)
    _style()
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ax, col, ylab in [(axes[0], "extra_income", "Extra lifetime income"),
                          (axes[1], "d_bequest", "Change in bequest")]:
        piv = a.pivot(index="balance", columns="death_age", values=col).loc[bals]
        series = [(piv[d].to_numpy(), SHADES[i], HATCHES[i], f"Death at {d}") for i, d in enumerate(p.death_ages)]
        bars, _, _ = _grouped_bars(ax, [_bal_label(b) for b in bals], series)
        _label_bars(ax, bars, fontsize=7)
        ax.set_ylabel(ylab, fontsize=11)
        ax.margins(y=0.18)
    axes[0].legend(frameon=False, fontsize=10, ncol=len(p.death_ages), loc="upper left")
    early = a[a["death_age"] == min(p.death_ages)]
    late = a[a["death_age"] == max(p.death_ages)]
    lbl = STYLE[scenario]["label"].lower() if scenario in STYLE else scenario
    title = (f"Early death costs the estate up to {_k(-early['d_bequest'].min())}; "
             f"living to {max(p.death_ages)} adds up to {_k(late['extra_income'].max())} of income")
    ft_header(fig, title,
              f"LIS case minus all ABP, {lbl}, undiscounted today's dollars, by age at death",
              SOURCE, right=0.97)
    fig.subplots_adjust(hspace=0.15)
    _save(fig, path, p)


def chart_neutrality_heatmap(matrix, within, same, default, p: Params, path, definition_label, weights_note=""):
    """4. Weighted cost difference (retargeted minus current) over cap x inc_pct_in.

    Boxed cells are within the tolerance; the final policy settings are labelled.
    """
    _style()
    fig, ax = plt.subplots(figsize=(10, 7))
    # $ thousands for large weighted sums (equal weights); whole dollars when weights are population shares
    scale, unit = (1000, "$k") if np.nanmax(np.abs(matrix.to_numpy())) >= 50_000 else (1, "$")
    vals = matrix.to_numpy() / scale
    lim = np.nanmax(np.abs(vals))
    im = ax.imshow(vals, cmap="cividis", aspect="auto", origin="lower", vmin=-lim, vmax=lim)
    ax.grid(False)
    ax.set_xticks(range(matrix.shape[1]))
    ax.set_xticklabels([f"{c:.0%}" for c in matrix.columns])
    ax.set_yticks(range(matrix.shape[0]))
    ax.set_yticklabels([_k(c) for c in matrix.index])
    ax.set_xlabel("Share of payments inside the cap counted under the income test")
    ax.set_ylabel("Real cap on concessional purchase amount")
    norm = im.norm
    for i in range(vals.shape[0]):
        for j in range(vals.shape[1]):
            v = vals[i, j]
            light = norm(v) > 0.6
            txt = "= now" if same.iloc[i, j] else f"{v:,.0f}"
            if default.iloc[i, j]:
                txt += "\nfinal"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    fontweight="bold" if default.iloc[i, j] else "normal", color="black" if light else "white")
            if within.iloc[i, j]:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor="black", linewidth=2.2))
                ax.add_patch(Rectangle((j - 0.42, i - 0.42), 0.84, 0.84, fill=False, edgecolor="white", linewidth=1))
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("Weighted cost difference, " + ("$ thousands" if scale == 1000 else "$"), fontsize=10)
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    cb.ax.tick_params(labelsize=9)
    n_new = int((within & ~same).to_numpy().sum())
    n_same = int((within & same).to_numpy().sum())
    title = (f"{n_new} new cap and income test setting{'s are' if n_new != 1 else ' is'} within "
             f"{p.neutrality_tolerance:.0%} of today's cost")
    sub = (f"{definition_label}: retargeted minus current PV Age Pension, {unit}. Box = within "
           f"{p.neutrality_tolerance:.0%}; 'final' = {_k(p.cap)}, {p.inc_pct_in:.0%}")
    if n_same:
        sub += "; '= now' = current rules"
    ft_header(fig, title, sub, SOURCE + weights_note, right=0.92)
    _save(fig, path, p)


def chart_sensitivity_return(by_r, p: Params, path):
    """5. Change in PV Age Pension at each tested real return, per scenario and balance."""
    scens = ["current_lis", "retargeted", "bonus"]
    bals = list(p.balances)
    rs = sorted(by_r["test_value"].unique())
    _style()
    fig, axes = plt.subplots(1, len(scens), figsize=(13, 6), sharey=True)
    for ax, s in zip(axes, scens):
        d = by_r[by_r["scenario"] == s].pivot(index="balance", columns="test_value", values="value").loc[bals]
        series = [(d[r].to_numpy(), SHADES[i], HATCHES[i], f"R = {r:.0%}") for i, r in enumerate(rs)]
        _grouped_bars(ax, [_bal_label(b) for b in bals], series)
        ax.set_title(STYLE[s]["label"], fontsize=12, color=FT_GREY, loc="left")
        ax.tick_params(axis="x", labelsize=9)
    axes[0].set_ylabel("Change in PV of Age Pension vs all ABP")
    axes[0].legend(frameon=False, fontsize=10, loc="upper left")
    cur = by_r[by_r["scenario"] == "current_lis"].groupby("test_value")["value"].mean()
    title = (f"Higher returns raise the Age Pension cost of a LIS: current settings average "
             f"{_k(cur.loc[min(rs)])} at R = {min(rs):.0%}, {_k(cur.loc[max(rs)])} at {max(rs):.0%}")
    if cur.loc[max(rs)] <= cur.loc[min(rs)]:
        title = (f"Higher returns lower the Age Pension cost of a LIS: current settings average "
                 f"{_k(cur.loc[min(rs)])} at R = {min(rs):.0%}, {_k(cur.loc[max(rs)])} at {max(rs):.0%}")
    ft_header(fig, title,
              "Change in PV of Age Pension vs all ABP by real net return R, today's dollars, other inputs at base. "
              "Bonus bars exclude the bonus payment",
              SOURCE, right=0.98)
    fig.subplots_adjust(top=0.80)
    _save(fig, path, p)


def _m(v):
    """$ million label, sign aware."""
    return f"-${-v / 1e6:,.1f}m" if v < 0 else f"${v / 1e6:,.1f}m"


def chart_equal_support(fiscal, p: Params, path, bonus_max, weights_note=""):
    """6. Equal support: for each policy, the change vs current settings in the lifetime government cost of
    10 years of new retirees at options_take_up, for the cohort and for all purchasers ($ million)."""
    pols = ["retargeted", "bonus", "bonus_flat"]
    f = fiscal[fiscal["take_up"].round(10) == round(p.options_take_up, 10)]
    tot = f.pivot(index="scenario", columns="group", values="lifetime_cost_undiscounted")
    d = tot.loc[pols] - tot.loc["current_lis"]
    names = {"retargeted": f"Retargeted\n(cap {_k(p.cap)}, {p.inc_pct_in:.0%})",
             "bonus": f"Equal support bonus\n({_k(bonus_max)}, tapered)",
             "bonus_flat": f"Flat {_k(p.bonus_flat_amount)} bonus\n(upper bound)"}
    coh = [b for b in p.cohort_balances]
    series = [(d["cohort"].to_numpy(), SHADES[0], HATCHES[0],
               f"Help to the cohort ({_k(min(coh))}-{_k(max(coh))})"),
              (d["all_purchasers"].to_numpy(), SHADES[1], HATCHES[1],
               f"Extra cost to government, all purchasers ({_bal_label(min(p.balances))}-{_bal_label(max(p.balances))})")]
    _style()
    fig, ax = plt.subplots(figsize=(10, 6.5))
    bars, _, _ = _grouped_bars(ax, [names[q] for q in pols], series, width=0.7)
    for container in bars:
        for rect in container:
            h = rect.get_height()
            ax.annotate(_m(h), (rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3 if h >= 0 else -3),
                        textcoords="offset points", ha="center", va="bottom" if h >= 0 else "top", fontsize=10,
                        color=FT_GREY)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"-${-v / 1e6:,.0f}m" if v < 0 else f"${v / 1e6:,.0f}m"))
    ax.set_ylabel("Change in 10 year lifetime government cost vs current")
    ax.tick_params(axis="x", labelsize=11)
    ax.legend(frameon=False, fontsize=10, loc="upper right")
    lo, hi = ax.get_ylim()
    ax.set_ylim(min(lo, -0.08 * hi), hi * 1.25)
    ret_all = d.loc["retargeted", "all_purchasers"]
    title = (f"Same cohort help ({_m(d.loc['retargeted', 'cohort'])}); extra cost: "
             f"retargeting {'+' if ret_all > 0 else ''}{_m(ret_all)}, "
             f"bonus +{_m(d.loc['bonus', 'all_purchasers'])}")
    ft_header(fig, title,
              f"Lifetime government cost (PV Age Pension + bonus) of {p.scale_up_years} years of new retirees "
              f"vs current settings, {p.options_take_up:.0%} take-up, $ million",
              SOURCE + weights_note, right=0.98)
    fig.subplots_adjust(bottom=0.15)
    _save(fig, path, p)


def chart_iris_gap(iris, p: Params, path):
    """7. Accumulation IRIS gap (retargeted_accum minus retargeted) by balance for each iris_years_cap,
    with the current rules gap (accum_iris minus current_lis) for comparison."""
    bals = list(p.balances)
    caps = list(p.sens_iris_years_cap)
    piv = iris.pivot(index="balance", columns="iris_years_cap", values="gap_retargeted").loc[bals]
    cur = iris.groupby("balance")["gap_current"].first().loc[bals]
    _style()
    fig, ax = plt.subplots(figsize=(10, 6))
    names = {k: (f"{k} years (default)" if k == p.iris_years_cap else
                 f"{k} years (no limit)" if k >= p.accum_years_held else f"{k} years") for k in caps}
    series = [(piv[k].to_numpy(), SHADES[i], HATCHES[i], names[k]) for i, k in enumerate(caps)]
    bars, x, _ = _grouped_bars(ax, [_bal_label(b) for b in bals], series)
    _label_bars(ax, [[r for r in c if abs(r.get_height()) >= 0.5] for c in bars], fontsize=7)
    for i, (xi, v) in enumerate(zip(x, cur.to_numpy())):
        ax.hlines(v, xi - 0.42, xi + 0.42, colors="black", linestyles="--", linewidth=1.6,
                  label="Current rules gap (accum_iris minus current_lis)" if i == 0 else None, zorder=6)
        if abs(v) < 500:
            continue
        ax.annotate(f"now {_k(v)}", (xi, v), xytext=(0, 4), textcoords="offset points", ha="center",
                    va="bottom", fontsize=8, fontweight="bold", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.15", fc=FT_CREAM, ec="none", alpha=0.85))
    ax.set_ylabel("Extra PV Age Pension from buying in accumulation")
    ax.legend(frameon=False, fontsize=9, loc="upper left", title="Deeming growth counted for",
              title_fontsize=9)
    ax.margins(y=0.12)
    top = iris[iris["iris_years_cap"] == p.iris_years_cap]["gap_retargeted"].max()
    title = (f"A {p.iris_years_cap} year limit holds the accumulation IRIS advantage to {_k(top)} "
             f"vs up to {_k(cur.max())} now")
    ft_header(fig, title,
              f"Change in PV Age Pension, bought {p.accum_years_held} years before 67 minus at 67, retargeted rules, "
              "today's dollars",
              SOURCE, right=0.97)
    _save(fig, path, p)
