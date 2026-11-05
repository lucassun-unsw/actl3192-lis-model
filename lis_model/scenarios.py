"""Scenario definitions.

A scenario says whether part of the balance goes into a LIS, which means test
rules apply to it, whether it was bought in accumulation, and whether a
government bonus is paid into it. Numeric settings live in `params.py`.
"""

from dataclasses import dataclass

from .params import Params


@dataclass(frozen=True)
class Scenario:
    name: str
    label: str
    lis: bool = False            # part of the balance goes into a LIS at 67
    rules: str = "current"       # "current" or "retargeted" LIS means test
    accumulation: bool = False   # LIS bought during accumulation (IRIS)
    bonus: bool = False          # government bonus paid into the LIS
    bonus_flat: bool = False     # flat bonus at every balance (no taper)


ALL_ABP = Scenario("all_abp", "All ABP")
CURRENT_LIS = Scenario("current_lis", "Current settings", lis=True)
ACCUM_IRIS = Scenario("accum_iris", "Current settings, bought in accumulation", lis=True, accumulation=True)
RETARGETED = Scenario("retargeted", "Retargeted", lis=True, rules="retargeted")
RETARGETED_ACCUM = Scenario("retargeted_accum", "Retargeted, bought in accumulation", lis=True,
                            rules="retargeted", accumulation=True)
BONUS = Scenario("bonus", "Bonus (equal support)", lis=True, bonus=True)
BONUS_FLAT = Scenario("bonus_flat", "Flat $10,000 bonus (upper bound)", lis=True, bonus=True, bonus_flat=True)

SCENARIOS = [ALL_ABP, CURRENT_LIS, ACCUM_IRIS, RETARGETED, RETARGETED_ACCUM, BONUS, BONUS_FLAT]
POLICIES = [s for s in SCENARIOS if s.lis]
BY_NAME = {s.name: s for s in SCENARIOS}


def bonus_amount(balance, p: Params, flat=False):
    """Bonus: bonus_max up to taper_start, linear taper to 0 at taper_end.
    Flat bonus: bonus_flat_amount at every balance."""
    if flat:
        return p.bonus_flat_amount
    if balance <= p.bonus_taper_start:
        return p.bonus_max
    if balance >= p.bonus_taper_end:
        return 0.0
    share = (p.bonus_taper_end - balance) / (p.bonus_taper_end - p.bonus_taper_start)
    return p.bonus_max * share


def recorded_ratio(years, p: Params):
    """Recorded / actual purchase amount for an accumulation IRIS held `years` years.

    The recorded amount grows at the upper deeming rate (nominal) while the
    actual amount grows at R real, so in today's dollars the ratio is
    ((1 + upper deeming) / ((1 + inflation)(1 + R)))^years.
    """
    g = (1 + p.deeming_upper) / ((1 + p.inflation) * (1 + p.real_return))
    return g ** years
