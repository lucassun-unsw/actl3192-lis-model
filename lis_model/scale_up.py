"""10 year fiscal cost scale up and take-up break even measures.

Lifetime cost of 10 years of new retirees = sum over entry years t = 1..10 of cost per
member x new retirees in cohort_t x take-up rate. Cost per member is the lifetime
government cost (PV at 67, today's dollars), so the total is the lifetime cost of ten
entry cohorts, not the cash spent inside a ten year budget window. The discounted total
discounts entry year t by (1 + real discount rate)^(t - 1) (first cohort retires now).
"""

import pandas as pd

from .inputs import homeowner_share_in_file, load_cohort_counts
from .params import Params
from .scenarios import BONUS, BONUS_FLAT, CURRENT_LIS, RETARGETED

SCALE_SCENARIOS = [CURRENT_LIS, RETARGETED, BONUS, BONUS_FLAT]
BREAK_EVEN_POLICIES = [RETARGETED, BONUS, BONUS_FLAT]
NOT_BINDING = "not binding"


def costed_counts(results: pd.DataFrame, counts: pd.DataFrame, scen, p: Params) -> pd.DataFrame:
    """Counts for entry years 1..scale_up_years with cost per member and entry year discount factor."""
    counts = counts[counts["year"].between(1, p.scale_up_years)]
    cost = results[results["scenario"] == scen.name].set_index("balance")["gov_cost"]
    c = counts.assign(cost_per_member=counts["balance_member"].map(cost))
    if c["cost_per_member"].isna().any():
        missing = sorted(c.loc[c["cost_per_member"].isna(), "balance_member"].unique())
        raise ValueError(f"No modelled member for balances {missing}")
    return c.assign(discount=1 / (1 + p.discount_rate) ** (c["year"] - 1))


def groups(p: Params):
    return {"all_purchasers": set(p.balances), "cohort": set(p.cohort_balances)}


def fiscal_cost(results: pd.DataFrame, counts: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Lifetime cost of 10 years of new retirees by scenario, take-up rate and member group."""
    rows = []
    for scen in SCALE_SCENARIOS:
        c = costed_counts(results, counts, scen, p)
        for group, bals in groups(p).items():
            g = c[c["balance_member"].isin(bals)]
            for rate in p.take_up_rates:
                cost = g["cost_per_member"] * g["count"] * rate
                rows.append({"scenario": scen.name, "group": group, "take_up": rate,
                             "entry_years": f"1 to {p.scale_up_years}",
                             "purchasers": float((g["count"] * rate).sum()),
                             "lifetime_cost_undiscounted": float(cost.sum()),
                             "lifetime_cost_discounted": float((cost * g["discount"]).sum())})
    return pd.DataFrame(rows)


def cost_per_buyer(c: pd.DataFrame, discounted=False) -> float:
    """Count weighted average lifetime cost per buyer over all entry years."""
    d = c["discount"] if discounted else 1.0
    return float((c["cost_per_member"] * c["count"] * d).sum() / (c["count"] * d).sum())


def break_even(results: pd.DataFrame, counts: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Break even take-up and marginal cost of take-up, all purchasers.

    u* = u0 x (cost per buyer, current settings) / (cost per buyer, policy): the take-up the policy
    can support for the same total cost as current settings at u0. "not binding" if the policy's
    cost per buyer is zero or negative (more buyers never cost more), or if current settings cost
    per buyer is not positive (there is no positive budget to match).
    Extra cost of 1 point of take-up = take_up_step x lifetime cost of all new retirees under the policy.
    """
    bals = groups(p)["all_purchasers"]
    cur = costed_counts(results, counts, CURRENT_LIS, p)
    cur = cur[cur["balance_member"].isin(bals)]
    rows = []
    for scen in BREAK_EVEN_POLICIES:
        pol = costed_counts(results, counts, scen, p)
        pol = pol[pol["balance_member"].isin(bals)]
        for u0 in p.take_up_rates:
            row = {"policy": scen.name, "group": "all_purchasers", "u0": u0}
            for tag, disc in [("", False), ("_discounted", True)]:
                c_cur, c_pol = cost_per_buyer(cur, disc), cost_per_buyer(pol, disc)
                binding = c_pol > 0 and c_cur > 0
                d = pol["discount"] if disc else 1.0
                row |= {f"cost_per_buyer_current{tag}": c_cur, f"cost_per_buyer_policy{tag}": c_pol,
                        f"break_even_take_up{tag}": u0 * c_cur / c_pol if binding else NOT_BINDING,
                        f"extra_cost_per_1pt_take_up{tag}": float((pol["cost_per_member"] * pol["count"] * d).sum()
                                                                  * p.take_up_step)}
            rows.append(row)
    return pd.DataFrame(rows)


def homeowner_sensitivity(results: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Fiscal totals with the homeowner share in the derived counts set to each tested value and
    the file value. Only the counts change; cost per member is unchanged, so totals scale with the share."""
    base = homeowner_share_in_file(p)
    frames = []
    for h in sorted(set(p.sens_homeowner_share) | {base}):
        counts, _ = load_cohort_counts(p, homeowner_share=h)
        frames.append(fiscal_cost(results, counts, p).assign(homeowner_share=h, is_base=abs(h - base) < 1e-12))
    out = pd.concat(frames, ignore_index=True)
    return out[["homeowner_share", "is_base", *[c for c in out.columns if c not in ("homeowner_share", "is_base")]]]
