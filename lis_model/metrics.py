"""Present values, bequest, cost per extra $ of income, and age of death outcomes."""

import pandas as pd

from .params import Params


def pv_age_pension(df):
    """sum tpx x v_t x Age Pension_t."""
    return float((df["tpx"] * df["discount"] * df["age_pension"]).sum())


def pv_income(df):
    """sum tpx x v_t x total income_t."""
    return float((df["tpx"] * df["discount"] * df["total_income"]).sum())


def pv_bequest(df, p: Params):
    """sum (prob die in year t) x v_t x ABP closing_t / (1 + disc).

    The bequest is the closing ABP balance of the year of death, paid at the end of that year.
    """
    return float((df["prob_die"] * df["discount"] * df["abp_close"]).sum() / (1 + p.discount_rate))


def summary(df, p: Params) -> dict:
    """Headline metrics for one projection."""
    first = df.iloc[0]
    return {
        "pv_age_pension": pv_age_pension(df),
        "pv_income": pv_income(df),
        "pv_bequest": pv_bequest(df, p),
        "age_pension_67": float(first["age_pension"]),
        "binding_test_67": first["binding_test"],
        "lis_purchase": df.attrs["purchase"],
        "bonus": df.attrs["bonus"],
        "first_lis_payment": df.attrs["first_payment"],
    }


def compare(policy, base, p: Params) -> dict:
    """Policy scenario metrics and changes vs the all ABP scenario.

    Government cost = change in PV Age Pension + any bonus paid at purchase.
    Cost per extra $1 of retiree income = government cost / change in PV income
    (equals change in PV AP / change in PV income when there is no bonus).
    """
    s, b = summary(policy, p), summary(base, p)
    d_ap = s["pv_age_pension"] - b["pv_age_pension"]
    d_inc = s["pv_income"] - b["pv_income"]
    gov_cost = d_ap + s["bonus"]
    return {
        **s,
        "age_pension_67_all_abp": b["age_pension_67"],
        "binding_test_67_all_abp": b["binding_test_67"],
        "d_pv_age_pension": d_ap,
        "d_pv_income": d_inc,
        "d_pv_bequest": s["pv_bequest"] - b["pv_bequest"],
        "gov_cost": gov_cost,
        "cost_per_extra_dollar_ap": d_ap / d_inc if d_inc > 0 else float("nan"),
        "cost_per_extra_dollar_gov": gov_cost / d_inc if d_inc > 0 else float("nan"),
    }


def age_of_death(policy, base, death_age) -> dict:
    """Undiscounted member outcome if death occurs at `death_age` (policy minus all ABP).

    Income is received for ages 67 to D - 1; the bequest is the ABP opening balance at age D.
    """
    alive = policy["age"] < death_age
    extra_income = float((policy.loc[alive, "total_income"] - base.loc[alive, "total_income"]).sum())
    at_d = policy["age"] == death_age
    if at_d.any():
        d_bequest = float(policy.loc[at_d, "abp_open"].iloc[0] - base.loc[at_d, "abp_open"].iloc[0])
    else:
        d_bequest = 0.0
    return {"death_age": death_age, "extra_income": extra_income, "d_bequest": d_bequest,
            "net_to_estate_and_member": extra_income + d_bequest}


def age_of_death_table(policy, base, p: Params) -> pd.DataFrame:
    return pd.DataFrame([age_of_death(policy, base, d) for d in p.death_ages])


def evaluate(p: Params, scenarios, balances=None):
    """Compare each policy scenario with all ABP for each member.

    Returns (results, age_of_death, projections): two tidy tables and a dict of
    projection tables keyed by (scenario name, balance).
    """
    from .projection import project
    from .scenarios import ALL_ABP

    balances = p.balances if balances is None else balances
    rows, aod, proj = [], [], {}
    for bal in balances:
        base = project(bal, ALL_ABP, p)
        proj[(ALL_ABP.name, bal)] = base
        rows.append({"scenario": ALL_ABP.name, "balance": bal, **compare(base, base, p)})
        for scen in scenarios:
            if not scen.lis:
                continue
            df = project(bal, scen, p)
            proj[(scen.name, bal)] = df
            rows.append({"scenario": scen.name, "balance": bal, **compare(df, base, p)})
            for r in age_of_death_table(df, base, p).to_dict("records"):
                aod.append({"scenario": scen.name, "balance": bal, **r})
    return pd.DataFrame(rows), pd.DataFrame(aod), proj
