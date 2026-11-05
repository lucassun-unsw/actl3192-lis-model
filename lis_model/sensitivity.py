"""One-at-a-time sensitivity tests (group decision: change one input, others at base)."""

import pandas as pd

from .metrics import evaluate
from .params import Params
from .scenarios import ALL_ABP, BONUS, CURRENT_LIS, RETARGETED

SENS_SCENARIOS = [ALL_ABP, CURRENT_LIS, RETARGETED, BONUS]

METRICS = ["age_pension_67", "pv_age_pension", "pv_income", "pv_bequest",
           "d_pv_age_pension", "d_pv_income", "d_pv_bequest", "gov_cost"]


def variations(p: Params):
    """(parameter, value) pairs: base run first, then each test value of each input."""
    tests = {"real_return": p.sens_real_return, "lis_allocation": p.sens_allocation,
             "discount_rate": p.sens_discount, "air": p.sens_air}
    out = [("base", None)]
    for name, values in tests.items():
        out += [(name, v) for v in values if v != getattr(p, name)]
    return out


def run_sensitivity(p: Params) -> pd.DataFrame:
    """Long table: parameter, test value, scenario, balance, metric, value."""
    frames = []
    for name, value in variations(p):
        q = p if name == "base" else p.with_(**{name: value})
        res, _, _ = evaluate(q, SENS_SCENARIOS)
        long = res.melt(id_vars=["scenario", "balance"], value_vars=METRICS, var_name="metric")
        long.insert(0, "test_value", value)
        long.insert(0, "parameter", name)
        frames.append(long)
    return pd.concat(frames, ignore_index=True)


def by_real_return(sens: pd.DataFrame, p: Params, metric="d_pv_age_pension") -> pd.DataFrame:
    """Metric at each tested R (base run supplies the base R)."""
    base = sens[(sens["parameter"] == "base") & (sens["metric"] == metric)].assign(test_value=p.real_return)
    var = sens[(sens["parameter"] == "real_return") & (sens["metric"] == metric)]
    return pd.concat([base, var], ignore_index=True).sort_values(["scenario", "balance", "test_value"])
