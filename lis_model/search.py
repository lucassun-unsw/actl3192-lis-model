"""Budget neutrality search for the retargeted policy.

Weighted cost = sum over members of weight x (PV AP under policy - PV AP under all ABP).
The retargeted policy is searched over a grid of cap x inc_pct_in, and combinations
within the tolerance of the current settings weighted cost are reported. The primary
definition is all purchasers ($400k to $1m); cohort only ($400k to $650k) is secondary.
A finer grid is searched around the chosen settings, and `choose_neutral_settings`
returns the combination closest to neutral for any set of weights.
"""

import pandas as pd

from .inputs import weight_map, with_weights
from .metrics import compare
from .params import BASE, Params
from .projection import project
from .scenarios import ALL_ABP, CURRENT_LIS, RETARGETED


def grid_values(start, stop, step):
    """Inclusive grid, rounded to avoid floating point drift."""
    n = int(round((stop - start) / step)) + 1
    return [round(start + i * step, 10) for i in range(n)]


def centred_values(centre, half_width, step, lower=0.0, upper=float("inf")):
    """Inclusive grid centre +/- half_width, clipped to [lower, upper]."""
    return [v for v in grid_values(centre - half_width, centre + half_width, step) if lower <= v <= upper]


def definitions(p: Params):
    """Member groups for the search, primary definition first: name -> balances."""
    groups = {"all_purchasers": tuple(p.balances), "cohort": tuple(p.cohort_balances)}
    return dict(sorted(groups.items(), key=lambda kv: kv[0] != p.neutrality_primary))


def definition_role(p: Params, name):
    return "primary" if name == p.neutrality_primary else "secondary"


def member_changes(p: Params, scen, balances):
    """Per member change in PV AP and PV income vs all ABP."""
    rows = []
    for bal in balances:
        c = compare(project(bal, scen, p), project(bal, ALL_ABP, p), p)
        rows.append({"balance": bal, "d_pv_age_pension": c["d_pv_age_pension"], "d_pv_income": c["d_pv_income"]})
    return pd.DataFrame(rows)


def weighted_cost(changes: pd.DataFrame, weights: dict):
    """sum weight x change in PV AP over the members in `changes`."""
    return float(sum(weights[b] * d for b, d in zip(changes["balance"], changes["d_pv_age_pension"])))


def same_as_current(p: Params, cap, pct, balances):
    """True when the combination reproduces current settings for every member in the group:
    no member's purchase exceeds the cap and the inside-cap income share equals the current one."""
    return cap >= max(balances) * p.lis_allocation and abs(pct - p.lis_income_share) < 1e-9


def run_grid(p: Params, caps=None, pcts=None, names=None) -> pd.DataFrame:
    """Weighted cost of every cap x inc_pct_in combination vs current settings.

    Defaults to the brief's grid and both definitions; `names` limits the definitions.
    """
    caps = grid_values(*p.grid_cap) if caps is None else caps
    pcts = grid_values(*p.grid_inc_pct) if pcts is None else pcts
    w = weight_map(p)
    rows = []
    for name, bals in definitions(p).items():
        if names is not None and name not in names:
            continue
        current = weighted_cost(member_changes(p, CURRENT_LIS, bals), w)
        for cap in caps:
            for pct in pcts:
                cost = weighted_cost(member_changes(p.with_(cap=cap, inc_pct_in=pct), RETARGETED, bals), w)
                diff = cost - current
                rows.append({"definition": name, "role": definition_role(p, name), "cap": cap, "inc_pct_in": pct,
                             "weighted_cost": cost, "current_weighted_cost": current,
                             "difference": diff, "pct_difference": diff / abs(current),
                             "within_tolerance": abs(diff) <= p.neutrality_tolerance * abs(current),
                             "same_as_current": same_as_current(p, cap, pct, bals),
                             "is_default": abs(cap - p.cap) < 1e-6 and abs(pct - p.inc_pct_in) < 1e-9})
    return pd.DataFrame(rows)


def fine_grid_axes(p: Params, cap=None, pct=None):
    """Fine grid values around (cap, pct), default the settings in p."""
    cap = p.cap if cap is None else cap
    pct = p.inc_pct_in if pct is None else pct
    return (centred_values(cap, *p.fine_cap, lower=p.fine_cap[1]),
            centred_values(pct, *p.fine_inc_pct, lower=0.0, upper=1.0))


def run_fine_grid(p: Params, cap=None, pct=None) -> pd.DataFrame:
    """Fine grid around the chosen settings, primary definition only, ranked by closeness to neutral.

    `closest_n` marks the n_best combinations closest to neutral (combinations that just
    reproduce current settings are never ranked).
    """
    caps, pcts = fine_grid_axes(p, cap, pct)
    g = run_grid(p, caps, pcts, names=[p.neutrality_primary])
    ranked = g[~g["same_as_current"]].assign(abs_diff=lambda d: d["difference"].abs()).sort_values("abs_diff")
    g["rank"] = pd.Series(range(1, len(ranked) + 1), index=ranked.index)
    g["closest_n"] = g["rank"] <= p.n_best
    return g.sort_values(["rank", "cap", "inc_pct_in"]).reset_index(drop=True)


def neutral_combinations(grid: pd.DataFrame) -> pd.DataFrame:
    """Combinations within tolerance, closest to neutral first."""
    out = grid[grid["within_tolerance"]].copy()
    out["abs_pct_difference"] = out["pct_difference"].abs()
    return out.sort_values(["definition", "abs_pct_difference"]).drop(columns="abs_pct_difference")


def best_combinations(grid: pd.DataFrame, n) -> pd.DataFrame:
    """The n combinations closest to neutral for each definition (within tolerance or not).

    Combinations that simply reproduce current settings are left out, as they shift nothing.
    """
    g = grid[~grid["same_as_current"]]
    g = g.assign(abs_diff=g["difference"].abs())
    return (g.sort_values(["definition", "abs_diff"]).groupby("definition", sort=False).head(n)
             .drop(columns="abs_diff").reset_index(drop=True))


def choose_neutral_settings(weights=None, p: Params = BASE) -> dict:
    """Retargeted settings closest to neutral (primary definition: all purchasers).

    `weights`: {balance: weight} or ((balance, weight), ...); None = the weights file.
    Searches the brief's grid, then the fine grid around the best coarse point, and
    returns the closest combination with its distance from current settings.
    Rerun this once real weights arrive, or set use_chosen_neutral = True in params.
    """
    if weights is not None:
        p = p.with_(weights=tuple(dict(weights).items()))
    p = with_weights(p)
    coarse = best_combinations(run_grid(p, names=[p.neutrality_primary]), 1).iloc[0]
    fine = best_combinations(run_fine_grid(p, coarse["cap"], coarse["inc_pct_in"]), 1).iloc[0]
    best = fine if abs(fine["difference"]) <= abs(coarse["difference"]) else coarse
    return {"definition": p.neutrality_primary, "cap": float(best["cap"]), "inc_pct_in": float(best["inc_pct_in"]),
            "weighted_cost": float(best["weighted_cost"]), "current_weighted_cost": float(best["current_weighted_cost"]),
            "difference": float(best["difference"]), "pct_difference": float(best["pct_difference"]),
            "within_tolerance": bool(best["within_tolerance"]),
            "coarse_cap": float(coarse["cap"]), "coarse_inc_pct_in": float(coarse["inc_pct_in"])}


def settings_check(p: Params) -> dict:
    """Weighted cost of the settings in p vs current settings (primary definition)."""
    g = run_grid(p, [p.cap], [p.inc_pct_in], names=[p.neutrality_primary]).iloc[0]
    return {k: g[k] for k in ["definition", "cap", "inc_pct_in", "weighted_cost", "current_weighted_cost",
                              "difference", "pct_difference", "within_tolerance"]}


def gains_shift(grid: pd.DataFrame, p: Params) -> pd.DataFrame:
    """How gains move between members under the closest-to-neutral combinations.

    For each of the n_best combinations per definition: each member's change in PV AP and PV
    income vs all ABP, under the retargeted combination and under current settings, and the
    difference (retargeted minus current).
    """
    w = weight_map(p)
    rows = []
    for _, b in best_combinations(grid, p.n_best).iterrows():
        bals = definitions(p)[b["definition"]]
        cur = member_changes(p, CURRENT_LIS, bals)
        ret = member_changes(p.with_(cap=b["cap"], inc_pct_in=b["inc_pct_in"]), RETARGETED, bals)
        for (_, c), (_, r) in zip(cur.iterrows(), ret.iterrows()):
            rows.append({
                "definition": b["definition"], "role": b["role"], "cap": b["cap"], "inc_pct_in": b["inc_pct_in"],
                "pct_difference": b["pct_difference"], "within_tolerance": b["within_tolerance"],
                "balance": c["balance"], "weight": w[c["balance"]],
                "d_pv_ap_current": c["d_pv_age_pension"], "d_pv_ap_retargeted": r["d_pv_age_pension"],
                "shift_pv_ap": r["d_pv_age_pension"] - c["d_pv_age_pension"],
                "d_pv_income_current": c["d_pv_income"], "d_pv_income_retargeted": r["d_pv_income"],
                "shift_pv_income": r["d_pv_income"] - c["d_pv_income"],
            })
    return pd.DataFrame(rows)


def heatmap_matrix(grid: pd.DataFrame, definition, values="difference") -> pd.DataFrame:
    """A grid column as cap rows x inc_pct_in columns."""
    g = grid[grid["definition"] == definition]
    return g.pivot(index="cap", columns="inc_pct_in", values=values).sort_index()
