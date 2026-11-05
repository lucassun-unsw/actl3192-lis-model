"""Policy checks: final retargeted settings and neutrality, equal support bonus solve,
IRIS limit, input files and break even take-up."""

import pandas as pd
import pytest

from lis_model import policies, scale_up, search
from lis_model.inputs import derived_counts, with_weights
from lis_model.params import BASE
from lis_model.scenarios import RETARGETED, RETARGETED_ACCUM

P = with_weights(BASE)


def test_default_settings_within_tolerance_of_current():
    """Final policy cap and inc_pct_in are within 2% of current settings (all purchasers, weights in use)."""
    check = search.settings_check(P)
    assert check["definition"] == "all_purchasers"
    assert abs(check["pct_difference"]) <= P.neutrality_tolerance, (
        f"Cap {P.cap:,.0f} / {P.inc_pct_in:.0%} is {check['pct_difference']:+.2%} from current settings")


def test_choose_neutral_settings_is_at_least_as_close_as_defaults():
    chosen = search.choose_neutral_settings(dict(P.weights), BASE)
    assert chosen["within_tolerance"]
    assert abs(chosen["difference"]) <= abs(search.settings_check(P)["difference"]) + 1e-6


def test_equal_support_bonus_matches_target():
    solve = policies.solve_bonus_max(P)
    assert solve["target"] > 0
    assert solve["achieved"] == pytest.approx(solve["target"], abs=1.0)


def test_iris_cap_limits():
    """Cap 0 = bought at 67; cap at or above years held = no limit."""
    bal = 650_000
    at_67 = policies.member_measures(P, RETARGETED, bal)["d_pv_age_pension"]
    cap0 = policies.member_measures(P.with_(iris_years_cap=0), RETARGETED_ACCUM, bal)["d_pv_age_pension"]
    full = policies.member_measures(P.with_(iris_years_cap=P.accum_years_held), RETARGETED_ACCUM, bal)
    beyond = policies.member_measures(P.with_(iris_years_cap=P.accum_years_held + 10), RETARGETED_ACCUM, bal)
    assert cap0 == pytest.approx(at_67, abs=1e-6)
    assert full["d_pv_age_pension"] == pytest.approx(beyond["d_pv_age_pension"], abs=1e-6)


def test_placeholder_derived_counts_equal_direct_placeholder():
    women, band, single, home = BASE.placeholder_cohort_inputs
    inputs = pd.DataFrame({"year": [1], "balance_member": [400_000], "women_turning_67": [women],
                           "share_in_band": [band], "single_share": [single], "homeowner_share": [home]})
    assert derived_counts(inputs)["count"].iloc[0] == pytest.approx(BASE.placeholder_count)


def test_break_even_formula():
    bals = list(BASE.balances)
    costs = {"current_lis": 100.0, "retargeted": 50.0, "bonus": 200.0, "bonus_flat": -10.0}
    results = pd.DataFrame([{"scenario": s, "balance": b, "gov_cost": c} for s, c in costs.items() for b in bals])
    counts = pd.DataFrame([{"year": t, "balance_member": b, "count": 10}
                           for t in range(1, BASE.scale_up_years + 1) for b in bals])
    be = scale_up.break_even(results, counts, BASE).set_index(["policy", "u0"])
    assert be.loc[("retargeted", 0.10), "break_even_take_up"] == pytest.approx(0.20)
    assert be.loc[("bonus", 0.10), "break_even_take_up"] == pytest.approx(0.05)
    assert be.loc[("bonus_flat", 0.10), "break_even_take_up"] == scale_up.NOT_BINDING
    n = 10 * len(bals) * BASE.scale_up_years
    assert be.loc[("bonus", 0.05), "extra_cost_per_1pt_take_up"] == pytest.approx(200.0 * n * BASE.take_up_step)


def test_final_policy_settings():
    """Final policy (group decision): cap $300,000, 40% income test inside the cap."""
    assert BASE.cap == 300_000
    assert BASE.inc_pct_in == pytest.approx(0.40)
    assert BASE.use_chosen_neutral is False
