"""Run every part of the model and write outputs/.

Usage (from the project folder):  python -m lis_model.run_all
"""

import contextlib
import io

import pandas as pd
import pytest

from . import charts, policies, scale_up, search, sensitivity
from .inputs import (ensure_input_files, homeowner_share_in_file, input_rows, load_cohort_counts,
                     load_cohort_inputs, load_weights, with_weights)
from .metrics import evaluate
from .mortality import life_expectancy, life_table
from .params import BASE, ROOT, Params, parameter_table
from .scenarios import SCENARIOS, recorded_ratio

OUT = ROOT / "outputs"

BASE_COLS = ["scenario", "balance", "lis_purchase", "bonus", "first_lis_payment",
             "age_pension_67_all_abp", "binding_test_67_all_abp", "age_pension_67", "binding_test_67",
             "pv_age_pension", "pv_income", "pv_bequest",
             "d_pv_age_pension", "d_pv_income", "d_pv_bequest", "gov_cost",
             "cost_per_extra_dollar_ap", "cost_per_extra_dollar_gov"]


def projections_table(proj) -> pd.DataFrame:
    """All year by year projections stacked into one long table."""
    frames = [df.assign(scenario=s, balance=b)[["scenario", "balance", *df.columns]] for (s, b), df in proj.items()]
    return pd.concat(frames, ignore_index=True)


def binding_years(proj) -> pd.DataFrame:
    """Years (ages 67 to 100) in which each test binds, by scenario and member."""
    rows = []
    for (s, b), df in proj.items():
        counts = df["binding_test"].value_counts()
        rows.append({"scenario": s, "balance": b, "at_67": df["binding_test"].iloc[0],
                     **{f"years_{k}": int(counts.get(k, 0)) for k in ("assets", "income", "nil")}})
    return pd.DataFrame(rows)


def write_tables(tables: dict):
    """CSV per table and one results.xlsx with a sheet per table.

    `tables`: name -> (DataFrame, note). The note goes in the first row of the sheet (the table
    starts on row 2) and as a `# ` comment on the first line of the CSV.
    """
    OUT.mkdir(exist_ok=True)
    with pd.ExcelWriter(OUT / "results.xlsx") as xw:
        for name, (df, note) in tables.items():
            with open(OUT / f"{name}.csv", "w") as f:
                f.write(f"# {note}\n")
                df.to_csv(f, index=False)
            sheet = name[:31]
            df.to_excel(xw, sheet_name=sheet, index=False, startrow=1)
            xw.sheets[sheet]["A1"] = note


def md_table(df: pd.DataFrame, fmt=None) -> str:
    """Plain markdown table (no tabulate dependency)."""
    fmt = fmt or {}
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = [fmt[c](r[c]) if c in fmt else str(r[c]) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def money(v):
    if isinstance(v, str):
        return v
    return "n/a" if pd.isna(v) else f"{v:,.0f}"


def usd(v):
    """Dollar amount for prose: $1,234 or -$1,234."""
    if isinstance(v, str) or pd.isna(v):
        return money(v)
    return f"-${-v:,.0f}" if v < 0 else f"${v:,.0f}"


def pct(v, digits=0):
    if isinstance(v, str):
        return v
    return "n/a" if pd.isna(v) else f"{v:.{digits}%}"


def ratio(v):
    return "n/a" if pd.isna(v) else f"{v:.2f}"


def kdollars(v):
    return f"${v / 1_000_000:g}m" if v >= 1_000_000 else f"${v / 1000:,.0f}k"


def group_labels(p: Params):
    """Labels for the two member groups, built from the parameters."""
    coh, allb = p.cohort_balances, p.balances
    return {"cohort": f"Cohort ({kdollars(min(coh))}-{kdollars(max(coh))})",
            "all_purchasers": f"All purchasers ({kdollars(min(allb))}-{kdollars(max(allb))})"}


def run_tests():
    """Run every test in tests/; returns (passed, pytest's last summary line)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pytest.main(["-q", "-p", "no:cacheprovider", str(ROOT / "tests")])
    lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
    return code == 0, lines[-1] if lines else ""


def prepare(p: Params):
    """Read the group inputs, apply the chosen retargeted settings and solve the bonus.

    Returns the parameters used for every result and a dict of run information.
    """
    ensure_input_files(p)
    weights, weights_ph = load_weights(p)
    p = with_weights(p)
    chosen = search.choose_neutral_settings(p=p)
    defaults = {"cap": p.cap, "inc_pct_in": p.inc_pct_in}
    if p.use_chosen_neutral:
        p = p.with_(cap=chosen["cap"], inc_pct_in=chosen["inc_pct_in"])
    check = search.settings_check(p)
    if p.bonus_design == "equal_support":
        solve = policies.solve_bonus_max(p)
        p = p.with_(bonus_max=solve["bonus_max"])
    elif p.bonus_design == "fixed":
        solve = {"target": policies.equal_support_target(p), "bonus_max": p.bonus_max,
                 "achieved": policies.cohort_support(p, policies.BONUS), "iterations": 0,
                 "note": "bonus_design = 'fixed': bonus_max taken from params, not solved"}
    else:
        raise ValueError(f"Unknown bonus_design '{p.bonus_design}'")
    counts, counts_ph = load_cohort_counts(p)
    cohort_inputs, _ = load_cohort_inputs(p)
    info = {"weights": weights, "weights_ph": weights_ph, "counts": counts, "counts_ph": counts_ph,
            "cohort_inputs": cohort_inputs,
            "counts_file": p.cohort_counts_file if p.count_source == "direct" else p.cohort_inputs_file,
            "chosen": chosen, "check": check, "solve": solve, "defaults": defaults}
    return p, info


def placeholder_note(info, needs):
    """Sentence naming the placeholder inputs a table depends on ('' if none)."""
    parts = []
    if "w" in needs and info["weights_ph"]:
        parts.append("population weights (inputs/weights.csv)")
    if "c" in needs and info["counts_ph"]:
        parts.append(f"cohort counts ({info['counts_file']})")
    return ("PLACEHOLDER-DEPENDENT: uses PLACEHOLDER " + " and ".join(parts) + ". Illustration only. "
            if parts else "")


def run(p: Params = BASE):
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("chart*.png"):
        old.unlink()
    p, info = prepare(p)
    results, aod, proj = evaluate(p, SCENARIOS)
    grid_all = search.run_grid(p)
    grid = grid_all[grid_all["definition"] == p.neutrality_primary].reset_index(drop=True)
    grid_sec = grid_all[grid_all["definition"] != p.neutrality_primary].reset_index(drop=True)
    neutral = search.neutral_combinations(grid)
    shift = search.gains_shift(grid, p)
    shift_sec = search.gains_shift(grid_sec, p)
    fine = search.run_fine_grid(p)
    fine_shift = search.gains_shift(fine, p)
    sens = sensitivity.run_sensitivity(p)
    fiscal = scale_up.fiscal_cost(results, info["counts"], p)
    hs = scale_up.homeowner_sensitivity(results, p) if p.count_source == "derived" else None
    be = scale_up.break_even(results, info["counts"], p)
    es = policies.bonus_equal_support_table(results, p, info["solve"])
    bm = policies.bonus_by_member(results, p)
    iris = policies.iris_cap_sensitivity(p)
    opts = policies.options_summary(results, fiscal, be, iris, p, info["solve"])
    binding = binding_years(proj)
    lt = life_table(p)
    chosen = pd.DataFrame([{"item": "settings used", **info["check"]},
                           {"item": "choose_neutral_settings()", **{k: v for k, v in info["chosen"].items()
                                                                     if not k.startswith("coarse")}}])

    pn = lambda needs: placeholder_note(info, needs)  # noqa: E731
    bonus_w = "Bonus rows use bonus_max solved under the weights. "
    lt_note = (f"Lifetime cost (PV at {p.retirement_age}, today's dollars) of {p.scale_up_years} years of new "
               f"retirees (entry years 1 to {p.scale_up_years}), NOT cash spent inside a {p.scale_up_years} year "
               f"window. Discounted: entry year t x 1/(1 + {p.discount_rate:.0%})^(t - 1). ")
    tables = {
        "base_results": (results[BASE_COLS], pn("w") + bonus_w + "Changes vs all ABP for the same member."),
        "age_of_death": (aod, pn("w") + bonus_w + "Undiscounted, LIS case minus all ABP."),
        "binding_tests": (binding, pn("w") + bonus_w + "Means test binding at 67 and years each test binds."),
        "sensitivity": (sens, pn("w") + bonus_w + "One input changed at a time; bonus_max held at the base solve."),
        "neutrality_grid": (grid, pn("w") + "PRIMARY definition: all purchasers. Retargeted minus current weighted cost."),
        "neutrality_within_2pct": (neutral, pn("w") + "PRIMARY definition: all purchasers. Combinations within "
                                   f"{p.neutrality_tolerance:.0%} of current settings."),
        "neutrality_gains_shift": (shift, pn("w") + f"PRIMARY definition: all purchasers. {p.n_best} combinations "
                                   "closest to neutral; shift = retargeted minus current."),
        "neutrality_fine_grid": (fine, pn("w") + "PRIMARY definition: all purchasers. Fine grid around the chosen "
                                 f"settings; closest_n = the {p.n_best} closest to neutral."),
        "neutrality_fine_gains_shift": (fine_shift, pn("w") + f"Gains shift for the {p.n_best} fine grid "
                                        "combinations closest to neutral (all purchasers)."),
        "neutrality_cohort_secondary": (grid_sec, pn("w") + "SECONDARY definition: cohort only ($400k to $650k)."),
        "gains_shift_cohort_secondary": (shift_sec, pn("w") + "SECONDARY definition: cohort only. Gains shift "
                                         "for the combinations closest to neutral."),
        "chosen_settings": (chosen, pn("w") + "Retargeted settings used, and the combination closest to neutral "
                            "(all purchasers) under the weights in use."),
        "bonus_equal_support": (es, pn("w") + f"bonus_max {usd(info['solve']['bonus_max'])} solved so the cohort "
                                f"gets the same weighted support as retargeting ({usd(info['solve']['target'])}). "
                                "Weighted sums; 'all' = all purchasers."),
        "bonus_by_member": (bm, pn("w") + "Age Pension clawback of the bonus by member, vs current settings."),
        "iris_cap_sensitivity": (iris, f"retargeted_accum by iris_years_cap; {p.accum_years_held} = no limit. "
                                 "gap = bought in accumulation minus bought at 67 (change in PV Age Pension)."),
        "fiscal_scale_up": (fiscal, pn("wc") + lt_note),
        **({"fiscal_homeowner_sensitivity": (hs, pn("wc") + "Homeowner share in the derived counts set to each "
                                             "value (fiscal scale up only; is_base = value in the inputs file). "
                                             + lt_note)} if hs is not None else {}),
        "take_up_break_even": (be, pn("wc") + "All purchasers. u* = u0 x cost per buyer (current) / cost per buyer "
                               f"(policy); extra cost per {p.take_up_step:.0%} point of take-up = lifetime cost of "
                               f"{p.scale_up_years} years of new retirees x {p.take_up_step:.0%}."),
        "options_summary": (opts, pn("wc") + "Weighted sums vs current settings use the weights; 10 year totals "
                            "are the lifetime cost of 10 years of new retirees. Simplicity and risk: "
                            + policies.NOT_SCORED + "."),
        "weights_used": (info["weights"], pn("w") + "Population weights per balance member."),
        "cohort_counts_used": (info["counts"], pn("c") + f"count_source = '{p.count_source}'."),
        "life_table": (lt, "ABS Life Tables 2022 to 2024, females, ages 67 to 100."),
        "projections": (projections_table(proj), pn("w") + bonus_w + "Every year by year projection, for audit."),
        "parameters": (pd.concat([parameter_table(p), input_rows(p)], ignore_index=True),
                       "Parameters used in this run, with source and evidence / judgement / placeholder label. cap, "
                       "inc_pct_in and bonus_max are the values actually used. Rows starting 'weights.csv' or "
                       "'cohort_inputs.csv' are the input file values, each with its own source."),
    }
    write_tables(tables)

    charts.chart_pv_age_pension(results, p, OUT / "chart1_change_pv_age_pension.png")
    charts.chart_ap_by_age(proj, p, OUT / "chart2_age_pension_by_age.png")
    charts.chart_age_of_death(aod, p, OUT / "chart3_age_of_death_current.png", "current_lis")
    charts.chart_age_of_death(aod, p, OUT / "chart3b_age_of_death_retargeted.png", "retargeted")
    charts.chart_age_of_death(aod, p, OUT / "chart3c_age_of_death_bonus.png", "bonus")
    labels = group_labels(p)
    wnote = " | weights are placeholders" if info["weights_ph"] else " | weights: ASFA 2026 Table 4"
    for g, d, fname in [(grid, p.neutrality_primary, f"chart4_neutrality_{p.neutrality_primary}.png"),
                        (grid_sec, grid_sec["definition"].iloc[0],
                         f"chart4b_neutrality_{grid_sec['definition'].iloc[0]}_secondary.png")]:
        mats = [search.heatmap_matrix(g, d, v) for v in ["difference", "within_tolerance", "same_as_current", "is_default"]]
        label = labels[d] + (" (primary)" if d == p.neutrality_primary else " (secondary)")
        charts.chart_neutrality_heatmap(*mats, p, OUT / fname, label, weights_note=wnote)
    charts.chart_sensitivity_return(sensitivity.by_real_return(sens, p), p, OUT / "chart5_sensitivity_return.png")
    charts.chart_equal_support(fiscal, p, OUT / "chart6_equal_support.png", info["solve"]["bonus_max"],
                               weights_note=wnote)
    charts.chart_iris_gap(iris, p, OUT / "chart7_iris_gap.png")

    recon = run_tests()
    write_summary(p, info, results, aod, binding, grid, grid_sec, neutral, shift, shift_sec, fine, fine_shift,
                  fiscal, hs, be, es, bm, iris, opts, recon)
    return tables


FMT = {c: money for c in ["lis_purchase", "bonus", "age_pension_67", "d_pv_age_pension", "d_pv_income",
                          "d_pv_bequest", "gov_cost", "extra_income", "d_bequest", "net_to_estate_and_member",
                          "weighted_cost", "current_weighted_cost", "difference", "d_pv_ap_current",
                          "d_pv_ap_retargeted", "shift_pv_ap", "d_pv_income_current", "d_pv_income_retargeted",
                          "shift_pv_income", "purchasers", "cap", "balance", "bonus_max", "d_pv_ap_vs_current",
                          "clawback", "net_gov_cost_vs_current", "d_pv_income_vs_current",
                          "d_pv_age_pension_retargeted_accum", "d_pv_age_pension_retargeted", "gap_retargeted",
                          "d_pv_age_pension_accum_iris", "d_pv_age_pension_current_lis", "gap_current",
                          "cost_per_buyer_current", "cost_per_buyer_policy"]}
FMT.update({"cost_per_extra_dollar_gov": ratio, "pct_difference": lambda v: f"{v:+.1%}",
            "inc_pct_in": lambda v: pct(v, 1 if round(v * 1000) % 10 else 0), "take_up": pct, "u0": pct,
            "break_even_take_up": lambda v: pct(v, 1), "clawback_share_of_bonus": pct,
            "iris_years_cap": lambda v: f"{v:.0f}", "rank": lambda v: f"{v:.0f}"})


def millions(v):
    if isinstance(v, str) or pd.isna(v):
        return money(v)
    return f"{v / 1e6:,.1f}"


def write_summary(p, info, results, aod, binding, grid, grid_sec, neutral, shift, shift_sec, fine, fine_shift,
                  fiscal, hs, be, es, bm, iris, opts, recon):
    """outputs/summary.md: final results for the group, headline findings first."""
    chosen, check, solve = info["chosen"], info["check"], info["solve"]
    w_ph, c_ph = info["weights_ph"], info["counts_ph"]
    tol = p.neutrality_tolerance
    wtxt = "PLACEHOLDER equal weights" if w_ph else "ASFA 2026 weights"
    rb = results.set_index(["scenario", "balance"])
    vs_cur = lambda s, b, m: rb.loc[(s, b), m] - rb.loc[("current_lis", b), m]  # noqa: E731
    es_r = es.set_index("policy")
    allp = fiscal[(fiscal["group"] == "all_purchasers")]
    f10 = allp[allp["take_up"].round(10) == round(p.options_take_up, 10)].set_index("scenario")
    be10 = be[be["u0"].round(10) == round(p.options_take_up, 10)].set_index("policy")["break_even_take_up"]
    ib = iris[(iris["balance"] == p.options_iris_balance) & iris["is_default"]].iloc[0]
    sign = lambda v: ("+" if v >= 0 else "") + usd(v)  # noqa: E731
    cohort, higher = list(p.cohort_balances), [b for b in p.balances if b not in p.cohort_balances]
    worse = [b for b in cohort if vs_cur("retargeted", b, "d_pv_age_pension") < 0]
    pct_take = pct(p.options_take_up)

    s = []
    s.append("# LIS model: final results (ACTL3192 Group 23)\n")
    s.append("Single female homeowners retiring at 67 with $400,000 to $650,000 in super (the cohort), plus "
             "$800,000 and $1m members to show who pays. All amounts are in today's dollars. Present values (PV) "
             f"are survival weighted from {p.retirement_age} with ABS 2022-24 female mortality and a "
             f"{p.discount_rate:.0%} real discount rate. Full tables are in `results.xlsx` (one sheet per table, "
             "a note in row 1) and the CSV files; charts are `chart1` to `chart7`.\n")
    if w_ph or c_ph:
        s.append("**Some inputs are still PLACEHOLDERS (see 'Placeholders'); results that depend on them are for "
                 "illustration only.**\n")

    # --- final policy and headline findings
    s.append("## Final policy\n")
    s.append(f"**Retargeted LIS means test: cap {usd(p.cap)} (real) on the purchase amount that gets concessional "
             f"treatment; inside the cap, {pct(p.inc_pct_in)} of payments count under the income test** (assets "
             f"{p.lis_asset_share_before:.0%}, {p.lis_asset_share_after:.0%} from {p.lis_threshold_age}, as now). "
             f"Above the cap the LIS is treated like an account-based pension. Accumulation purchases count at most "
             f"{p.iris_years_cap} years of deeming growth.\n")
    s.append("## Headline findings\n")
    s.append(f"- **Budget neutral.** Across all purchasers ({wtxt}) the final policy costs {sign(check['difference'])} "
             f"per woman aged 65 to 69 with super vs current settings ({check['pct_difference']:+.2%}), "
             + ("within" if check["within_tolerance"] else "**NOT within**") + f" the {tol:.0%} neutrality band.")
    s.append("- **The cohort gains, higher balances pay.** Change in PV Age Pension vs current settings: "
             + "; ".join(f"{_bal(b)} {sign(vs_cur('retargeted', b, 'd_pv_age_pension'))}" for b in p.balances)
             + ". " + ("Every cohort member is better off than under current settings."
                       if not worse else "Cohort members worse off: " + ", ".join(_bal(b) for b in worse) + "."))
    s.append(f"- **A bonus giving the cohort the same help costs much more.** The equal support bonus "
             f"({usd(solve['bonus_max'])} up to {usd(p.bonus_taper_start)}, tapering to nil at "
             f"{usd(p.bonus_taper_end)}) is new spending of {usd(es_r.loc['bonus', 'all_d_gov_cost_vs_current'])} "
             f"per woman 65 to 69 with super, against {sign(es_r.loc['retargeted', 'all_d_gov_cost_vs_current'])} "
             f"for retargeting, for the same {usd(solve['target'])} of help to the cohort. A flat "
             f"{usd(p.bonus_flat_amount)} bonus (upper bound) costs {usd(es_r.loc['bonus_flat', 'all_d_gov_cost_vs_current'])} "
             f"but gives the cohort only {usd(es_r.loc['bonus_flat', 'cohort_d_gov_cost_vs_current'])}.")
    s.append(f"- **Fiscal cost.** Lifetime cost of {p.scale_up_years} years of new retirees at {pct_take} take-up, all "
             "purchasers, undiscounted: " + ", ".join(
                 f"{lbl} ${f10.loc[sc, 'lifetime_cost_undiscounted'] / 1e6:,.1f}m"
                 for sc, lbl in [("current_lis", "current settings"), ("retargeted", "retargeted"),
                                 ("bonus", "equal support bonus"), ("bonus_flat", "flat bonus")]) + ".")
    s.append(f"- **Take-up.** For the same total cost as current settings at {pct_take} take-up, retargeting supports "
             f"{pct(be10['retargeted'], 1)} take-up, the equal support bonus {pct(be10['bonus'], 1)} and the flat "
             f"bonus {pct(be10['bonus_flat'], 1)}.")
    s.append(f"- **Accumulation purchases.** At {_bal(p.options_iris_balance)}, buying the LIS {p.accum_years_held} "
             f"years early adds {usd(ib['gap_current'])} of PV Age Pension under current rules and "
             f"{usd(ib['gap_retargeted'])} under the final policy ({p.iris_years_cap} year limit).")
    s.append("- **Members' income.** For the bonus, the Age Pension falls through the clawback even though the "
             f"member's total income rises (at {_bal(cohort[0])}: PV Age Pension "
             f"{sign(vs_cur('bonus', cohort[0], 'd_pv_age_pension'))}, PV retiree income "
             f"{sign(vs_cur('bonus', cohort[0], 'd_pv_income'))} vs current settings).\n")

    s.append("## How to read the numbers\n")
    s.append("- 'vs all ABP' = the scenario minus the same member keeping the whole balance in an account-based "
             "pension; 'vs current' = minus the same member under current settings (50% in a LIS at 67).")
    s.append("- Government cost = change in PV Age Pension, plus the bonus for the bonus options.")
    wsum = info["weights"]["weight"].sum()
    s.append(f"- 'Weighted' = sum over members of population weight x value. The weights are the share of women "
             f"aged 65 to 69 with super in each balance band and add to {wsum:.3f}, so a weighted figure is per "
             "woman aged 65 to 69 with super (counting only the five modelled bands).")
    s.append(f"- Fiscal totals are the **lifetime** cost of everyone retiring in entry years 1 to {p.scale_up_years}, "
             f"not cash spent inside a {p.scale_up_years} year window; discounted totals use "
             f"1/(1 + {p.discount_rate:.0%})^(t - 1) for entry year t.\n")

    # --- options table
    s.append("## Options assessment\n")
    o = opts.copy()
    cols = [c for c in o.columns if c not in ("scenario", "equity_iris_gap_basis", "simplicity", "risk", "note")]
    ofmt = {c: (millions if "10y" in c else money) for c in cols[1:]}
    ofmt[[c for c in cols if c.startswith("take_up")][0]] = lambda v: "" if pd.isna(v) else pct(v, 1)
    s.append(md_table(o[cols].rename(columns=lambda c: c.replace("_", " ")),
                      {k.replace("_", " "): (lambda f: (lambda v: "" if (not isinstance(v, str) and pd.isna(v))
                                                        else f(v)))(f) for k, f in ofmt.items()}) + "\n")
    s.append("10 year columns in $ million; other money columns in $ (weighted columns per woman 65 to 69 with "
             "super). Equity: 'age pension only' = change in PV Age Pension vs all ABP (government spending on the "
             "member, not the member's whole outcome); 'retiree income' = change in PV of drawdowns + LIS payments + "
             "Age Pension vs current settings. The IRIS gap for the bonus options is the current rules gap, as the "
             "bonus keeps current means test rules. Simplicity and risk are left for the group to score "
             "(High / Medium / Low) in the `options_summary` sheet. Deferred annuity: considered, not modelled.\n")

    # --- results by member
    s.append("## Results by member\n")
    s.append("Changes vs all ABP. `bonus` = equal support bonus, `bonus_flat` = flat bonus upper bound, "
             "`*_accum` / `accum_iris` = LIS bought 20 years before 67. `cost_per_extra_dollar_gov` = government "
             "cost / change in PV income.\n")
    key = results[results["scenario"] != "all_abp"][
        ["scenario", "balance", "lis_purchase", "bonus", "age_pension_67", "binding_test_67",
         "d_pv_age_pension", "d_pv_income", "d_pv_bequest", "gov_cost", "cost_per_extra_dollar_gov"]]
    s.append(md_table(key, FMT) + "\n")
    s.append(f"Means test binding at {p.retirement_age} (full year by year counts in `binding_tests`):\n")
    b67 = binding.pivot(index="scenario", columns="balance", values="at_67").loc[binding["scenario"].unique()]
    b67.columns = [_bal(b) for b in b67.columns]
    s.append(md_table(b67.reset_index()) + "\n")
    s.append("### Outcomes by age of death (undiscounted, vs all ABP)\n")
    s.append(md_table(aod[aod["scenario"].isin(["current_lis", "retargeted", "bonus"])], FMT) + "\n")

    # --- neutrality
    s.append("## Budget neutrality (all purchasers)\n")
    s.append(f"Current settings weighted cost: {usd(grid['current_weighted_cost'].iloc[0])} per woman 65 to 69 with "
             f"super. Grid: cap {usd(p.grid_cap[0])} to {usd(p.grid_cap[1])} step {usd(p.grid_cap[2])}; income test "
             f"share {pct(p.grid_inc_pct[0])} to {pct(p.grid_inc_pct[1])} step {pct(p.grid_inc_pct[2])}. Settings "
             f"within {tol:.0%} of current settings (heatmap: chart 4):\n")
    s.append(md_table(neutral[["cap", "inc_pct_in", "weighted_cost", "difference", "pct_difference"]], FMT) + "\n")
    caps, pcts = search.fine_grid_axes(p)
    s.append(f"Fine grid around the final policy (cap {usd(min(caps))} to {usd(max(caps))}, {pct(min(pcts))} to "
             f"{pct(max(pcts))}), five closest to neutral:\n")
    s.append(md_table(fine[fine["closest_n"]][["rank", "cap", "inc_pct_in", "difference", "pct_difference",
                                               "within_tolerance", "is_default"]].rename(
        columns={"is_default": "final_policy"}), FMT) + "\n")
    s.append(f"The closest combination, cap {usd(chosen['cap'])} / {pct(chosen['inc_pct_in'], 1)} "
             f"({chosen['pct_difference']:+.2%}), is shown for reference; the group chose cap {usd(p.cap)} / "
             f"{pct(p.inc_pct_in)}. How the final policy moves Age Pension between members (retargeted minus "
             "current, per member; retiree income moves by the same amount, as only the Age Pension changes):\n")
    mv = pd.DataFrame([{"balance": b, "d_pv_ap_current": rb.loc[("current_lis", b), "d_pv_age_pension"],
                        "d_pv_ap_retargeted": rb.loc[("retargeted", b), "d_pv_age_pension"],
                        "shift_pv_ap": vs_cur("retargeted", b, "d_pv_age_pension")} for b in p.balances])
    s.append(md_table(mv, FMT) + "\n")
    s.append(f"Secondary definition, cohort only: current settings weighted cost "
             f"{usd(grid_sec['current_weighted_cost'].iloc[0])}; full grid in `neutrality_cohort_secondary`.\n")

    # --- bonus
    s.append("## Equal support bonus\n")
    s.append(f"Equal total cost would set the bonus to zero, because retargeting is budget neutral. Instead the bonus "
             f"is sized to give the cohort the same help: the weighted change in government cost for the cohort "
             f"under retargeting is {usd(solve['target'])}; keeping the taper, bisection gives bonus_max = "
             f"**{usd(solve['bonus_max'])}** (chart 6).\n")
    es_md = es[["policy", "bonus_max", "cohort_d_gov_cost_vs_current", "all_d_gov_cost_vs_current",
                "cohort_income_per_1_cost_vs_current", "all_income_per_1_cost_vs_current",
                "cohort_income_per_1_cost_vs_all_abp", "all_income_per_1_cost_vs_all_abp"]]
    s.append(md_table(es_md, {**FMT, **{c: money for c in es_md.columns[1:4]},
                              **{c: ratio for c in es_md.columns[4:]}}) + "\n")
    s.append("'income per $1 of cost vs current' = extra PV retiree income / extra government cost relative to current "
             "settings (n/a where the cost change is about zero); 'vs all ABP' = PV income gained / total government "
             "cost of the LIS. The bonus gives a little more than $1 of income per $1 of cost because the extra LIS "
             f"payments are priced at the {p.air:.0%} AIR but rise with R = {p.real_return:.0%}, which outweighs the "
             f"{p.loading:.0%} loading.\n")
    inc_bound = bm[(bm["policy"] == "bonus") & (bm["binding_test_67_bonus"] == "income")]["balance"]
    s.append("**Clawback.** The bonus raises the LIS purchase amount and payments. For income test members (at 67: "
             f"{', '.join(_bal(b) for b in inc_bound) or 'none'}) the extra payments reduce the Age Pension; for "
             "assets test members the larger assessed purchase amount does. Part of each bonus dollar comes back as "
             "lower Age Pension:\n")
    s.append(md_table(bm[bm["bonus"] > 0][["policy", "balance", "binding_test_67_bonus", "bonus", "clawback",
                                            "clawback_share_of_bonus", "net_gov_cost_vs_current",
                                            "d_pv_income_vs_current"]], FMT) + "\n")

    # --- IRIS
    s.append("## Accumulation IRIS limit\n")
    s.append(f"Gap = extra PV Age Pension from buying the LIS {p.accum_years_held} years before 67 instead of at 67. "
             f"Under current rules the recorded purchase amount grows at the {p.deeming_upper:.2%} deeming rate, "
             "below actual growth, so buying early lowers the assessed asset. The final policy counts at most "
             f"{p.iris_years_cap} years of deeming growth ({p.accum_years_held} = no limit; chart 7):\n")
    s.append(md_table(iris[["balance", "iris_years_cap", "gap_retargeted", "gap_current"]], FMT) + "\n")

    # --- fiscal
    s.append(f"## Fiscal cost: lifetime cost of {p.scale_up_years} years of new retirees ($ million)\n")
    counts = info["counts"]
    per_year = counts.groupby("year")["count"].sum().iloc[0]
    s.append(f"New single homeowner retirees a year across the five members: {per_year:,.0f}. All purchasers:\n")
    s.append(md_table(allp.drop(columns=["group", "entry_years"]),
                      {**FMT, "lifetime_cost_undiscounted": millions, "lifetime_cost_discounted": millions}) + "\n")
    if hs is not None:
        base_h = homeowner_share_in_file(p)
        s.append(f"Homeowner share sensitivity (base {base_h:.3f}; single older women are likely to own less often "
                 "than all households aged 65 to 74). Totals scale in proportion; $ million, all purchasers:\n")
        h = hs[hs["group"] == "all_purchasers"]
        piv = h.pivot_table(index=["scenario", "take_up"], columns="homeowner_share",
                            values=["lifetime_cost_undiscounted", "lifetime_cost_discounted"], sort=False)
        piv.columns = [f"{'undiscounted' if a.endswith('undiscounted') else 'discounted'} at {b:.3f}"
                       for a, b in piv.columns]
        piv = piv[sorted(piv.columns, key=lambda c: (not c.startswith("undiscounted"), c))].reset_index()
        s.append(md_table(piv, {**FMT, **{c: millions for c in piv.columns[2:]}}) + "\n")

    # --- take-up
    s.append("## Take-up break even (all purchasers)\n")
    s.append("Break even take-up u* = u0 x (cost per buyer, current settings) / (cost per buyer, policy): the take-up "
             "the policy can reach for the same total cost as current settings at take-up u0 (above u0 = cheaper per "
             "buyer). 'not binding' would mean the policy's cost per buyer is zero or negative. Extra cost of one more "
             f"point of take-up = {p.take_up_step:.0%} x lifetime cost of all new retirees under the policy "
             "($ million).\n")
    s.append(md_table(be[["policy", "u0", "cost_per_buyer_current", "cost_per_buyer_policy", "break_even_take_up",
                          "extra_cost_per_1pt_take_up", "extra_cost_per_1pt_take_up_discounted"]],
                      {**FMT, "extra_cost_per_1pt_take_up": millions,
                       "extra_cost_per_1pt_take_up_discounted": millions}) + "\n")

    # --- data, assumptions, limitations
    s.append("## Data and assumptions\n")
    inp = info["cohort_inputs"]
    s.append("Evidence based: Services Australia Age Pension and deeming rates from 20 September 2026; DSS LIS means "
             "test rules; minimum drawdown rates; ABS Life Tables 2022-24 (females).\n")
    s.append(f"Judgement: real return {p.real_return:.0%} (ABP and LIS), inflation {p.inflation:.1%}, AIR "
             f"{p.air:.0%}, loading {p.loading:.0%}, {p.lis_allocation:.0%} of the balance in the LIS, real discount "
             f"rate {p.discount_rate:.0%}; Age Pension settings constant in real terms.\n")
    s.append("Population and counts:")
    s.append("- Weights: ASFA 2026 Table 4 (ATO 2% sample, women 65 to 69 with super, June 2024): "
             + ", ".join(f"{_bal(b)} {x:.4f}" for b, x in zip(info["weights"]["balance_member"],
                                                               info["weights"]["weight"])) + ".")
    s.append(f"- New retirees a year = women reaching 67 with super ({inp['women_turning_67'].iloc[0]:,.0f}; ASFA 2026 "
             f"Table 1) x band share (as the weights) x single share ({inp['single_share'].iloc[0]:.3f}; ABS 2021 "
             f"Census G06) x homeowner share ({inp['homeowner_share'].iloc[0]:.3f}; ABS HOC 2019-20 Table 6.1).\n")
    s.append("Every parameter, input value and source is in the `parameters` sheet.\n")
    s.append("### Limitations\n")
    s.append("\n".join(f"- {c}" for c in data_limitations(p)) + "\n")
    s.append("### Modelling choices\n")
    s.append("\n".join(f"{i}. {c}" for i, c in enumerate(modelling_choices(p, solve), 1)) + "\n")

    s.append("## Placeholders\n")
    if w_ph or c_ph:
        s.append("Still PLACEHOLDER: " + ", ".join(x for x, f in [("population weights", w_ph),
                                                                   ("cohort counts", c_ph)] if f) + ".\n")
    else:
        s.append("None in use. (`inputs/cohort_counts.csv` keeps placeholder direct counts but is not used.)\n")

    s.append("## Model checks\n")
    passed, line = recon
    if passed:
        s.append(f"All tests pass ({line}). The model reproduces the group's Excel model: every reconciliation "
                 "target within $5 and every projection cell of the Excel `Member_*` sheets within $0.000001. Model "
                 f"life expectancy at {p.retirement_age} is {life_expectancy(p):.2f} (ABS 88.0; the table ends at "
                 f"{p.max_age}). Other tests check the final policy settings and its neutrality, the equal support "
                 "solve, the IRIS limit, the input data and the homeowner sensitivity.\n")
    else:
        s.append(f"**Tests FAILED ({line}). Do not use these results until they pass.**\n")
    s.append("Rerun everything with `python -m lis_model.run_all`.\n")
    (OUT / "summary.md").write_text("\n".join(s))


def data_limitations(p: Params):
    """Limitations of the weights and cohort inputs (Updates 2 and 3)."""
    return [
        "Balances are for all women aged 65 to 69 with super, not only single homeowners at 67.",
        "Band shares are interpolated between the published percentiles (ASFA 2026 Table 4); the $1m band is "
        "extrapolated beyond the 90th percentile.",
        "The single share uses ages 65 to 74, not 67 exactly.",
        "The homeowner share is for all households with a reference person aged 65 to 74, not single women; single "
        "older women are likely to own less often, hence the 0.717 and 0.767 sensitivity.",
        "Census 2021 and HOC 2019-20 are older than the June 2024 super data.",
        "Counts assume single homeowners have the same balance distribution as all women aged 65 to 69 with super.",
        "Members are stylised: everyone in a band is modelled at the band's single balance.",
    ]


def _bal(b):
    return f"${b / 1e6:g}m" if b >= 1_000_000 else f"${b / 1000:,.0f}k"


def modelling_choices(p: Params, solve):
    return [
        "**Core logic copied from the Excel model.** Drawdowns and LIS payments at the start of each year; "
        "LIS priced as a life annuity due at the AIR using the same ABS mortality; payments then move with "
        "(1 + R) / (1 + AIR); the LIS purchase amount is fixed in nominal terms, so its assessed value shrinks "
        f"by inflation ({p.inflation:.1%}) each year in today's dollars. Life table ends at {p.max_age}; anyone "
        f"alive at {p.max_age} is treated as dying during that year.",
        f"**Accumulation IRIS (scenario 3).** The LIS value at {p.retirement_age} equals the same "
        f"{p.lis_allocation:.0%} allocation, so payments are "
        "identical to current settings; only the assessed purchase amount differs. Recorded / actual = "
        f"((1 + {p.deeming_upper:.2%}) / ((1 + {p.inflation:.1%})(1 + R)))^{p.accum_years_held} = "
        f"{recorded_ratio(p.accum_years_held, p):.3f} at R = {p.real_return:.0%}"
        + (" (deeming growth is lower than actual nominal growth), so the assessed asset is smaller and the "
           "member receives more Age Pension." if recorded_ratio(p.accum_years_held, p) < 1 else
           " (deeming growth is higher than actual nominal growth), so the assessed asset is larger and the "
           "member receives less Age Pension.")
        + f" The threshold age stays {p.lis_threshold_age} (later "
        f"of {p.lis_threshold_age} and 5 years after purchase).",
        f"**Retargeted policy above the cap (group decision).** The recorded purchase amount is split once, at "
        f"{p.retirement_age}: inside = min(purchase, cap {usd(p.cap)}), above = the rest. Inside: assets "
        f"{p.lis_asset_share_before:.0%} ({p.lis_asset_share_after:.0%} from {p.lis_threshold_age}), income "
        f"{pct(p.inc_pct_in)} of the related payments. Above: {p.above_cap_asset_share:.0%} of the amount counts as "
        f"an asset and {p.above_cap_income_share:.0%} of the related payments as income. Both parts are deflated by "
        "inflation each year, as under current rules. Payments are split in the same proportion as the purchase amount.",
        "**Retargeted policy for an accumulation purchase (group decision).** Scenario `retargeted_accum`. "
        f"Deeming growth is counted for min({p.accum_years_held}, iris_years_cap = {p.iris_years_cap}) years; the cap "
        "is applied to the recorded (deeming grown) amount. Used in the IRIS cap sensitivity, chart 7 and the options "
        f"summary; the sensitivity tests, neutrality search and other charts use the purchase at {p.retirement_age}.",
        f"**Equal support bonus.** Bonus based on the balance at {p.retirement_age} before the bonus, added to the LIS "
        "purchase, so it is reduced by the product loading and assessed under both tests as part of the purchase; "
        "the ABP part is unchanged. Government cost = bonus + change in PV Age Pension. bonus_max is solved by "
        f"bisection to within ${p.bonus_solve_tol:g} ({solve['iterations']} steps) so the weighted cohort change in "
        "government cost vs current settings equals that of the retargeted policy. The solve is done once at base "
        "inputs; the sensitivity tests hold this bonus_max fixed (a dollar bonus would not be re-set when returns "
        "change).",
        "**Retiree income per $1 of government cost** is shown two ways: relative to current settings (extra "
        "income / extra cost; n/a for a budget neutral policy, whose extra cost is about zero; for retargeting it "
        "is 1.00 whenever defined, because only the Age Pension changes) and relative to all ABP (total). "
        "Government cost per extra $1 of income in `base_results` is n/a where retiree income does not rise.",
        f"**Budget neutrality.** Weighted cost = sum of weight x change in PV Age Pension (weights in "
        f"`inputs/weights.csv`); the {p.neutrality_tolerance:.0%} band is relative to the current settings "
        "weighted cost of the same member group. 'Closest' combinations exclude those that reproduce current "
        "settings exactly. All 'weighted' figures elsewhere are weighted sums with the same weights.",
        "**Sensitivity (group decision).** One input changed at a time, others at base. Changing R also changes the "
        "all ABP comparison, so changes are always against all ABP under the same inputs.",
        f"**Fiscal scale up.** Cost per member is a lifetime PV at {p.retirement_age}, so totals are the lifetime "
        f"cost of {p.scale_up_years} years of new retirees, not cash spent inside a {p.scale_up_years} year window. "
        f"Discounted totals discount entry year t by (1 + {p.discount_rate:.0%})^(t - 1) (first cohort retires now). "
        "The same take-up rate is applied to every balance. Members are stylised: each count is assumed to have "
        "exactly that balance. Break even take-up and the marginal cost use the cohort counts (not the weights) so "
        "they match the fiscal totals.",
        f"**Options summary.** Fiscal and income columns are weighted sums vs current settings; 10 year totals at "
        f"{pct(p.options_take_up)} take-up, all purchasers. Equity is shown two ways: change in PV Age Pension vs all ABP (Age Pension only) and change in PV retiree income vs current settings. The "
        f"IRIS gap for the bonus options is the current rules gap, because the bonus keeps current means test rules "
        "(a bonus paid into an accumulation purchase is not modelled).",
        f"**Charts** follow ft_style_graph.md but are saved at {p.chart_dpi} dpi as the brief asks, and use hatching, "
        "line styles and markers so they read in black and white. The heatmap uses the cividis colour map, whose "
        "lightness changes evenly, with values printed in every cell.",
    ]


if __name__ == "__main__":
    run()
    print(f"Outputs written to {OUT}")
