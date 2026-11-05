"""Year by year projection for one member under one scenario.

Ages 67 to 100, annual steps, all amounts in today's dollars (real terms).
Drawdowns and LIS payments are at the start of each year. Logic follows the
Excel model (`Member_*` sheets) exactly for the all ABP and current LIS cases.
"""

import numpy as np
import pandas as pd

from . import means_test as mt
from .mortality import life_table
from .scenarios import Scenario, bonus_amount, recorded_ratio
from .params import Params


def min_drawdown_rate(ages, p: Params):
    """Minimum drawdown % by age at the start of the year."""
    from_ages = np.array([a for a, _ in p.min_drawdown])
    rates = np.array([r for _, r in p.min_drawdown])
    idx = np.searchsorted(from_ages, ages, side="right") - 1
    if np.any(idx < 0):
        raise ValueError("Age below the first minimum drawdown band")
    return rates[idx]


def annuity_factor(tpx, rate):
    """Life annuity due factor: sum_t tpx(t) / (1 + rate)^t."""
    t = np.arange(len(tpx))
    return float(np.sum(tpx / (1 + rate) ** t))


def lis_payments(purchase, tpx, p: Params):
    """LIS payments by year: priced at the AIR, then move with (1 + R) / (1 + AIR)."""
    factor = annuity_factor(tpx, p.air)
    first = purchase * (1 - p.loading) / factor if factor > 0 else 0.0
    t = np.arange(len(tpx))
    return first * ((1 + p.real_return) / (1 + p.air)) ** t, factor, first


def lis_assessment_current(recorded, payments, ages, p: Params):
    """Current rules: assets = recorded purchase deflated to today's dollars x 60% (30% from
    the threshold age); income = 60% of gross payments."""
    t = np.arange(len(ages))
    share = np.where(ages < p.lis_threshold_age, p.lis_asset_share_before, p.lis_asset_share_after)
    assets = recorded / (1 + p.inflation) ** t * share
    income = p.lis_income_share * payments
    return assets, income


def lis_assessment_retargeted(recorded, payments, ages, p: Params):
    """Retargeted rules. The recorded purchase amount is split once, at 67, at the real cap.

    Inside the cap: assets as now (60%, 30% from the threshold age), income = inc_pct_in
    of the related payments. Above the cap: treated like an ABP, so above_cap_asset_share
    (100%) of the amount counts as an asset and above_cap_income_share (100%) of the related
    payments as income. Both parts are deflated by inflation each year, as in current rules.
    Payments are split in the same proportion as the recorded amount.
    """
    t = np.arange(len(ages))
    inside = min(recorded, p.cap)
    above = recorded - inside
    share_in = inside / recorded if recorded > 0 else 1.0
    asset_share = np.where(ages < p.lis_threshold_age, p.lis_asset_share_before, p.lis_asset_share_after)
    deflator = (1 + p.inflation) ** t
    assets = (inside * asset_share + above * p.above_cap_asset_share) / deflator
    income = payments * (share_in * p.inc_pct_in + (1 - share_in) * p.above_cap_income_share)
    return assets, income


def recorded_purchase(scen: Scenario, purchase, p: Params):
    """Purchase amount recorded for the assets test.

    Accumulation IRIS: grows at the upper deeming rate for the years held (current rules)
    or at most iris_years_cap years (retargeted rules).
    """
    if not scen.accumulation:
        return purchase
    years = p.accum_years_held
    if scen.rules == "retargeted":
        years = min(years, p.iris_years_cap)
    return purchase * recorded_ratio(years, p)


def lis_assessment(scen: Scenario, purchase, payments, ages, p: Params):
    """Assessed LIS assets and income under the scenario's rules."""
    recorded = recorded_purchase(scen, purchase, p)
    if scen.rules == "current":
        return lis_assessment_current(recorded, payments, ages, p)
    if scen.rules == "retargeted":
        return lis_assessment_retargeted(recorded, payments, ages, p)
    raise ValueError(f"Unknown LIS rules '{scen.rules}'")


def project(balance, scen: Scenario, p: Params) -> pd.DataFrame:
    """Projection table for one member. Scalars are stored in `df.attrs`."""
    lt = life_table(p)
    ages, t, tpx = lt["age"].to_numpy(), lt["t"].to_numpy(), lt["tpx"].to_numpy()
    n = len(ages)

    lis_amount = balance * p.lis_allocation if scen.lis else 0.0
    bonus = bonus_amount(balance, p, scen.bonus_flat) if scen.bonus else 0.0
    purchase = lis_amount + bonus
    if scen.lis:
        payments, factor, first = lis_payments(purchase, tpx, p)
        lis_assets, lis_income = lis_assessment(scen, purchase, payments, ages, p)
    else:
        payments, factor, first = np.zeros(n), annuity_factor(tpx, p.air), 0.0
        lis_assets, lis_income = np.zeros(n), np.zeros(n)

    draw_rate = min_drawdown_rate(ages, p)
    abp_open, drawdown, abp_close = np.zeros(n), np.zeros(n), np.zeros(n)
    bal = balance - lis_amount
    for i in range(n):
        abp_open[i] = bal
        drawdown[i] = bal * draw_rate[i]
        abp_close[i] = (bal - drawdown[i]) * (1 + p.real_return)
        bal = abp_close[i]

    deemed = mt.deemed_income(abp_open, p)
    assessed_assets = abp_open + lis_assets
    assessed_income = deemed + lis_income
    ap, ap_at, ap_it, binding = mt.age_pension(assessed_assets, assessed_income, p)

    df = pd.DataFrame({
        "age": ages, "t": t, "tpx": tpx, "prob_die": lt["prob_die"].to_numpy(),
        "discount": 1 / (1 + p.discount_rate) ** t, "min_draw_pct": draw_rate,
        "abp_open": abp_open, "drawdown": drawdown, "deemed_income": deemed,
        "lis_payment": payments, "lis_assessed_assets": lis_assets, "lis_assessed_income": lis_income,
        "assessed_assets": assessed_assets, "assessed_income": assessed_income,
        "ap_assets_test": ap_at, "ap_income_test": ap_it, "age_pension": ap, "binding_test": binding,
        "total_income": drawdown + payments + ap, "abp_close": abp_close,
    })
    df.attrs.update(balance=balance, scenario=scen.name, lis_amount=lis_amount, bonus=bonus,
                    purchase=purchase, annuity_factor=factor, first_payment=first,
                    recorded_purchase=recorded_purchase(scen, purchase, p) if scen.lis else 0.0)
    return df
