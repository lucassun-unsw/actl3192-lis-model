"""Policy comparisons added in Update 1.

- Equal support bonus: solve bonus_max (bisection) so the bonus gives the cohort the
  same weighted change in government cost, vs current settings, as the retargeted policy.
- Bonus clawback by member, accumulation IRIS cap sensitivity, and the options summary.

"Weighted" always means sum over members of weight x value, with the weights in use.
"vs current" means policy minus current settings for the same member (both measured
against all ABP, so the all ABP terms cancel).
"""

import pandas as pd

from .inputs import weight_map
from .metrics import compare
from .params import Params
from .projection import project
from .scenarios import (ACCUM_IRIS, ALL_ABP, BONUS, BONUS_FLAT, CURRENT_LIS, RETARGETED,
                        RETARGETED_ACCUM)

MEASURES = ["gov_cost", "d_pv_income", "d_pv_age_pension"]
NOT_SCORED = "to be scored by the group (High / Medium / Low)"


def member_measures(p: Params, scen, bal) -> dict:
    """gov_cost, d_pv_income and d_pv_age_pension vs all ABP for one member."""
    c = compare(project(bal, scen, p), project(bal, ALL_ABP, p), p)
    return {m: c[m] for m in MEASURES} | {"bonus": c["bonus"], "binding_test_67": c["binding_test_67"]}


def weighted_vs_current(results: pd.DataFrame, scenario, balances, weights, measure="gov_cost"):
    """sum weight x (measure under scenario - measure under current settings)."""
    r = results.set_index(["scenario", "balance"])[measure]
    return float(sum(weights[b] * (r[(scenario, b)] - r[(CURRENT_LIS.name, b)]) for b in balances))


def weighted_vs_abp(results: pd.DataFrame, scenario, balances, weights, measure="gov_cost"):
    """sum weight x measure (already a change vs all ABP)."""
    r = results.set_index(["scenario", "balance"])[measure]
    return float(sum(weights[b] * r[(scenario, b)] for b in balances))


def cohort_support(p: Params, scen) -> float:
    """Weighted change in government cost over the cohort, scen minus current settings."""
    w = weight_map(p)
    return float(sum(w[b] * (member_measures(p, scen, b)["gov_cost"] - member_measures(p, CURRENT_LIS, b)["gov_cost"])
                     for b in p.cohort_balances))


def equal_support_target(p: Params) -> float:
    """Money the retargeted policy moves to the cohort, vs current settings (weighted)."""
    return cohort_support(p, RETARGETED)


def solve_bonus_max(p: Params) -> dict:
    """bonus_max (taper shape kept) giving the cohort the same weighted support as retargeting.

    Bisection on [0, hi]; hi starts at bonus_solve_start and doubles until it brackets the target.
    Support rises with the bonus because the Age Pension clawback is always less than the bonus.
    """
    target = equal_support_target(p)
    support = lambda b: cohort_support(p.with_(bonus_max=b), BONUS)  # noqa: E731
    if target <= 0:
        return {"target": target, "bonus_max": 0.0, "achieved": 0.0, "iterations": 0,
                "note": "Retargeting moves no money to the cohort, so the equal support bonus is zero"}
    lo, hi = 0.0, p.bonus_solve_start
    while support(hi) < target:
        lo, hi = hi, hi * 2
    n = 0
    while hi - lo > p.bonus_solve_tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if support(mid) < target else (lo, mid)
        n += 1
    b = (lo + hi) / 2
    return {"target": target, "bonus_max": b, "achieved": support(b), "iterations": n, "note": ""}


def bonus_equal_support_table(results: pd.DataFrame, p: Params, solve: dict) -> pd.DataFrame:
    """One row per policy: cost and income vs current settings and vs all ABP, and income per $1 of cost.

    Income per $1 vs current is left blank where the policy is budget neutral (cost change within
    the neutrality tolerance of the current weighted cost), since dividing by about zero means nothing.
    """
    w = weight_map(p)
    groups = {"cohort": p.cohort_balances, "all": p.balances}
    rows = []
    for scen in [CURRENT_LIS, RETARGETED, BONUS, BONUS_FLAT]:
        row = {"policy": scen.name, "label": scen.label,
               "bonus_max": solve["bonus_max"] if scen is BONUS else (p.bonus_flat_amount if scen is BONUS_FLAT else 0.0)}
        for g, bals in groups.items():
            cur_cost = weighted_vs_abp(results, CURRENT_LIS.name, bals, w)
            d_cost = weighted_vs_current(results, scen.name, bals, w)
            d_inc = weighted_vs_current(results, scen.name, bals, w, "d_pv_income")
            cost = weighted_vs_abp(results, scen.name, bals, w)
            inc = weighted_vs_abp(results, scen.name, bals, w, "d_pv_income")
            neutral = abs(d_cost) <= p.neutrality_tolerance * abs(cur_cost)
            row |= {f"{g}_d_gov_cost_vs_current": d_cost, f"{g}_d_pv_income_vs_current": d_inc,
                    f"{g}_income_per_1_cost_vs_current": float("nan") if neutral else d_inc / d_cost,
                    f"{g}_gov_cost_vs_all_abp": cost, f"{g}_d_pv_income_vs_all_abp": inc,
                    f"{g}_income_per_1_cost_vs_all_abp": inc / cost if cost > 0 else float("nan")}
        rows.append(row)
    return pd.DataFrame(rows)


def bonus_by_member(results: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Per member: bonus, Age Pension clawback (fall in PV AP vs current settings), net cost.

    Clawback: the bonus raises the LIS purchase, so assessed assets and (for income test bound
    members) assessed LIS payments rise, and the Age Pension falls.
    """
    r = results.set_index(["scenario", "balance"])
    rows = []
    for scen in [BONUS, BONUS_FLAT]:
        for b in p.balances:
            s, c = r.loc[(scen.name, b)], r.loc[(CURRENT_LIS.name, b)]
            d_ap = s["d_pv_age_pension"] - c["d_pv_age_pension"]
            rows.append({"policy": scen.name, "balance": b, "binding_test_67_current": c["binding_test_67"],
                         "binding_test_67_bonus": s["binding_test_67"], "bonus": s["bonus"],
                         "d_pv_ap_vs_current": d_ap, "clawback": -d_ap,
                         "clawback_share_of_bonus": -d_ap / s["bonus"] if s["bonus"] > 0 else float("nan"),
                         "net_gov_cost_vs_current": s["gov_cost"] - c["gov_cost"],
                         "d_pv_income_vs_current": s["d_pv_income"] - c["d_pv_income"]})
    return pd.DataFrame(rows)


def iris_cap_sensitivity(p: Params) -> pd.DataFrame:
    """retargeted_accum for each tested iris_years_cap, and the gap vs buying at 67.

    gap_retargeted = retargeted_accum - retargeted; gap_current = accum_iris - current_lis
    (current rules count all accum_years_held years, so it does not depend on the cap).
    """
    rows = []
    for b in p.balances:
        ret = member_measures(p, RETARGETED, b)["d_pv_age_pension"]
        cur = member_measures(p, CURRENT_LIS, b)["d_pv_age_pension"]
        acc = member_measures(p, ACCUM_IRIS, b)["d_pv_age_pension"]
        for k in p.sens_iris_years_cap:
            ra = member_measures(p.with_(iris_years_cap=k), RETARGETED_ACCUM, b)["d_pv_age_pension"]
            rows.append({"balance": b, "iris_years_cap": k, "years_counted": min(k, p.accum_years_held),
                         "is_default": k == p.iris_years_cap,
                         "d_pv_age_pension_retargeted_accum": ra, "d_pv_age_pension_retargeted": ret,
                         "gap_retargeted": ra - ret, "d_pv_age_pension_accum_iris": acc,
                         "d_pv_age_pension_current_lis": cur, "gap_current": acc - cur})
    return pd.DataFrame(rows)


def options_summary(results, fiscal, break_even, iris, p: Params, solve: dict) -> pd.DataFrame:
    """Options assessment table: one row per option, numbers from the other tables."""
    w = weight_map(p)
    r = results.set_index(["scenario", "balance"])
    allp = fiscal[(fiscal["group"] == "all_purchasers") & (fiscal["take_up"].round(10) == round(p.options_take_up, 10))]
    allp = allp.set_index("scenario")
    be = break_even[break_even["u0"].round(10) == round(p.options_take_up, 10)].set_index("policy")
    ib = iris[(iris["balance"] == p.options_iris_balance) & (iris["is_default"])].iloc[0]
    iris_gap = {CURRENT_LIS.name: (ib["gap_current"], "accum_iris minus current_lis"),
                RETARGETED.name: (ib["gap_retargeted"], f"retargeted_accum minus retargeted, iris_years_cap {p.iris_years_cap}"),
                BONUS.name: (ib["gap_current"], "as current settings: the bonus keeps current means test rules "
                                                 "(bonus not modelled for accumulation purchases)"),
                BONUS_FLAT.name: (ib["gap_current"], "as current settings: the bonus keeps current means test rules "
                                                      "(bonus not modelled for accumulation purchases)")}
    notes = {CURRENT_LIS.name: "Baseline (50% in a LIS at 67, current means test)",
             RETARGETED.name: f"Cap ${p.cap:,.0f}, {p.inc_pct_in:.0%} income test inside cap; budget neutral by design",
             BONUS.name: f"bonus_max ${solve['bonus_max']:,.0f} (solved), taper ${p.bonus_taper_start:,.0f} to "
                         f"${p.bonus_taper_end:,.0f}; same cohort support as retargeting",
             BONUS_FLAT.name: f"Flat ${p.bonus_flat_amount:,.0f} at every balance; upper bound"}
    labels = {CURRENT_LIS.name: "Current settings", RETARGETED.name: "Retargeted",
              BONUS.name: "Bonus, equal support", BONUS_FLAT.name: f"Bonus, flat ${p.bonus_flat_amount:,.0f}"}
    pct = f"{p.options_take_up:.0%}"
    rows = []
    for s in [CURRENT_LIS.name, RETARGETED.name, BONUS.name, BONUS_FLAT.name]:
        cur_total = allp.loc[CURRENT_LIS.name]
        row = {
            "option": labels[s], "scenario": s,
            "fiscal_d_gov_cost_vs_current_weighted_all": weighted_vs_current(results, s, p.balances, w),
            f"fiscal_10y_lifetime_cost_{pct}_undiscounted": allp.loc[s, "lifetime_cost_undiscounted"],
            f"fiscal_10y_lifetime_cost_{pct}_discounted": allp.loc[s, "lifetime_cost_discounted"],
            f"fiscal_10y_vs_current_{pct}_undiscounted": allp.loc[s, "lifetime_cost_undiscounted"]
                                                         - cur_total["lifetime_cost_undiscounted"],
            "income_d_pv_income_vs_current_weighted_cohort": weighted_vs_current(results, s, p.cohort_balances, w, "d_pv_income"),
            "income_d_pv_income_vs_current_weighted_all": weighted_vs_current(results, s, p.balances, w, "d_pv_income"),
        }
        for b in p.cohort_balances:
            row[f"equity_age_pension_only_d_pv_vs_all_abp_{b // 1000}k"] = r.loc[(s, b), "d_pv_age_pension"]
        for b in p.cohort_balances:
            row[f"equity_retiree_income_d_pv_vs_current_{b // 1000}k"] = (r.loc[(s, b), "d_pv_income"]
                                                                         - r.loc[(CURRENT_LIS.name, b), "d_pv_income"])
        row[f"equity_iris_gap_{p.options_iris_balance // 1000}k"] = iris_gap[s][0]
        row["equity_iris_gap_basis"] = iris_gap[s][1]
        row[f"take_up_break_even_u0_{pct}"] = p.options_take_up if s == CURRENT_LIS.name else be.loc[s, "break_even_take_up"]
        row["simplicity"] = NOT_SCORED
        row["risk"] = NOT_SCORED
        row["note"] = notes[s]
        rows.append(row)
    rows.append({"option": "Deferred annuity", "scenario": "", "note": "considered, not modelled"})
    return pd.DataFrame(rows)
