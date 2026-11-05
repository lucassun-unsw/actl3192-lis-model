"""Input checks: real population weights and cohort inputs, and the homeowner share sensitivity."""

import pandas as pd
import pytest

from lis_model import scale_up
from lis_model.inputs import load_cohort_counts, load_cohort_inputs, load_weights
from lis_model.metrics import evaluate
from lis_model.params import BASE
from lis_model.scenarios import CURRENT_LIS, RETARGETED


def test_inputs_are_not_placeholders():
    assert not load_weights(BASE)[1]
    assert BASE.count_source == "derived"
    assert not load_cohort_counts(BASE)[1]


def test_cohort_inputs_values():
    df, _ = load_cohort_inputs(BASE)
    assert (df["women_turning_67"] == 99_106).all()
    assert df["single_share"].eq(0.385).all()
    assert df["homeowner_share"].eq(0.817).all()
    for c in ["women_source", "band_source", "single_source", "homeowner_source"]:
        assert df[c].notna().all() and not df[c].str.contains("PLACEHOLDER").any()


def test_band_shares_match_weights():
    w = load_weights(BASE)[0].set_index("balance_member")["weight"]
    df, _ = load_cohort_inputs(BASE)
    assert df["share_in_band"].to_numpy() == pytest.approx(df["balance_member"].map(w).to_numpy())


def test_derived_counts_formula():
    counts, _ = load_cohort_counts(BASE)
    w = load_weights(BASE)[0].set_index("balance_member")["weight"]
    expected = 99_106 * counts["balance_member"].map(w) * 0.385 * 0.817
    assert counts["count"].to_numpy() == pytest.approx(expected.to_numpy())


def test_homeowner_sensitivity_scales_in_proportion():
    results, _, _ = evaluate(BASE, [CURRENT_LIS, RETARGETED])
    results = pd.concat([results, results[results["scenario"] == "current_lis"].assign(scenario="bonus"),
                         results[results["scenario"] == "current_lis"].assign(scenario="bonus_flat")])
    hs = scale_up.homeowner_sensitivity(results, BASE)
    assert sorted(hs["homeowner_share"].unique()) == pytest.approx([0.717, 0.767, 0.817])
    key = ["scenario", "group", "take_up"]
    base = hs[hs["is_base"]].set_index(key)["lifetime_cost_undiscounted"]
    for h in BASE.sens_homeowner_share:
        alt = hs[hs["homeowner_share"] == h].set_index(key)["lifetime_cost_undiscounted"]
        assert (alt / base).to_numpy() == pytest.approx(h / 0.817)
