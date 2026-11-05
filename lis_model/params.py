"""All model parameters in one place.

Every field carries metadata with its source and whether it is evidence based
("evidence"), a judgement assumption ("judgement"), or a placeholder still to be
supplied by the group ("placeholder"). `parameter_table()` turns this into the
parameters sheet of results.xlsx.
"""

from dataclasses import dataclass, field, fields, replace
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

SA = "Services Australia, rates from 20 Sep 2026"
UPDATE1 = "Group decision, Update 1"
UPDATE2 = "Group decision, Update 2"
UPDATE3 = "Group decision, Update 3"
DSS_LIS = "DSS means test rules for lifetime income streams; Reading 1; Week 5 lecture"


def _p(default, source, label, note=""):
    """Dataclass field with source / evidence label metadata."""
    meta = {"source": source, "label": label, "note": note}
    if isinstance(default, (list, dict, tuple)):
        return field(default_factory=lambda: default, metadata=meta)
    return field(default=default, metadata=meta)


@dataclass(frozen=True)
class Params:
    # --- Age Pension means test (evidence) ---
    max_rate_fn: float = _p(1237.70, SA, "evidence", "Maximum single rate incl. supplements, $ a fortnight")
    fortnights: int = _p(26, "Convention used in Excel model", "evidence", "Fortnights per year")
    assets_free_area: float = _p(333_000, SA, "evidence", "Assets test free area, single homeowner")
    assets_taper_fn_per_1000: float = _p(3.0, SA, "evidence", "$ a fortnight per $1,000 over free area")
    income_free_area_fn: float = _p(226, SA, "evidence", "Income test free area, $ a fortnight")
    income_taper: float = _p(0.5, SA, "evidence", "Pension reduction per $1 of income over free area")
    deeming_threshold: float = _p(66_800, SA, "evidence", "Deeming threshold, single")
    deeming_lower: float = _p(0.0175, SA, "evidence", "Deeming rate below threshold")
    deeming_upper: float = _p(0.0375, SA, "evidence", "Deeming rate above threshold")

    # --- LIS means test (evidence) ---
    lis_asset_share_before: float = _p(0.60, DSS_LIS, "evidence", "Share of purchase amount assessed as asset before threshold age")
    lis_asset_share_after: float = _p(0.30, DSS_LIS, "evidence", "Share of purchase amount assessed as asset from threshold age")
    lis_threshold_age: int = _p(84, "Week 5 lecture", "evidence", "Later of 84 and 5 years after purchase")
    lis_income_share: float = _p(0.60, DSS_LIS, "evidence", "Share of gross LIS payments assessed as income")
    min_drawdown: tuple = _p(((65, 0.05), (75, 0.06), (80, 0.07), (85, 0.09), (90, 0.11), (95, 0.14)),
                             "Week 5 lecture", "evidence", "(from age, minimum %) at start of year")

    # --- Mortality (evidence) ---
    life_table_file: str = _p("Data/3302055001DO001_20222024.xlsx", "ABS Life Tables 2022 to 2024", "evidence", "")
    life_table_sheet: str = _p("Table 9", "ABS Life Tables 2022 to 2024", "evidence", "")
    life_table_age_col: str = _p("A", "ABS Table 9 layout", "evidence", "Age column")
    life_table_lx_col: str = _p("F", "ABS Table 9 layout", "evidence", "Female lx column")
    life_table_first_row: int = _p(8, "ABS Table 9 layout", "evidence", "Row holding age 0")
    retirement_age: int = _p(67, "Age Pension age", "evidence", "")
    max_age: int = _p(100, "ABS Table 9 last age", "evidence", "Projection ends at the last ABS age")

    # --- Judgement assumptions ---
    real_return: float = _p(0.03, "Judgement", "judgement", "Real net return R, ABP and LIS share the same portfolio. Test 0% and 6%")
    inflation: float = _p(0.025, "Judgement", "judgement", "Only used to shrink the fixed nominal LIS purchase amount in real terms")
    air: float = _p(0.02, "Judgement, as in Conexus", "judgement", "LIS assumed investment return, real")
    loading: float = _p(0.05, "Judgement", "judgement", "LIS product loading")
    lis_allocation: float = _p(0.50, "Judgement, follows Conexus 50% split", "judgement", "Share of balance at 67 put into LIS")
    discount_rate: float = _p(0.02, "Judgement", "judgement", "Real discount rate for present values")

    # --- Members ---
    cohort_balances: tuple = _p((400_000, 500_000, 650_000), "Group cohort definition", "judgement", "Single female homeowners, $400k to $650k")
    higher_balances: tuple = _p((800_000, 1_000_000), "Group choice", "judgement", "Higher balance members, used to show who pays")
    death_ages: tuple = _p((75, 90, 100), "Group choice", "judgement", "Ages of death for member equity outcomes")

    # --- Accumulation IRIS (scenario 3) ---
    accum_years_held: int = _p(20, "Group choice", "judgement", "Years the LIS is held before 67 when bought in accumulation")

    # --- Retargeted policy (scenario 4) ---
    cap: float = _p(300_000, "FINAL POLICY (group decision after Update 3)", "judgement",
                    "Real cap on purchase amount given concessional treatment")
    inc_pct_in: float = _p(0.40, "FINAL POLICY (group decision after Update 3; was 35% in Update 1)", "judgement",
                           "Share of payments inside the cap assessed as income")
    use_chosen_neutral: bool = _p(False, "Modelling switch (Update 1)", "judgement",
                                  "True = run_all replaces cap and inc_pct_in with choose_neutral_settings() under the weights in use")
    iris_years_cap: int = _p(5, UPDATE1, "judgement", "Max years of deeming growth counted for accumulation IRIS (retargeted_accum)")
    sens_iris_years_cap: tuple = _p((0, 5, 10, 20), UPDATE1, "judgement",
                                    "iris_years_cap values tested for retargeted_accum (20 = no limit, same as current rules)")
    above_cap_asset_share: float = _p(1.0, "Modelling choice (brief); deflation treatment confirmed by group", "judgement",
                                      "Share of the above-cap purchase amount (split at 67, deflated by inflation like the rest) assessed as an asset")
    above_cap_income_share: float = _p(1.0, "Modelling choice (brief)", "judgement",
                                       "Share of payments related to the above-cap amount assessed as income")

    # --- Bonus policy (scenario 5) ---
    bonus_design: str = _p("equal_support", UPDATE1, "judgement",
                           "'equal_support' = run_all solves bonus_max (bisection) so the cohort gets the same weighted "
                           "support as under the retargeted policy; 'fixed' = use bonus_max as given")
    bonus_max: float = _p(5_000, "Solved by run_all for equal support with the retargeted policy (Update 1 design); "
                          "5,000 here is only the old placeholder, used if bonus_design = 'fixed'",
                          "judgement", "Government bonus paid into LIS at purchase, full rate")
    bonus_taper_start: float = _p(400_000, UPDATE1 + ": keep taper shape", "judgement", "Balance at which bonus starts to taper")
    bonus_taper_end: float = _p(700_000, UPDATE1 + ": keep taper shape", "judgement", "Balance at which bonus reaches zero")
    bonus_flat_amount: float = _p(10_000, UPDATE1 + ": upper bound sensitivity", "judgement",
                                  "Flat bonus paid at every balance, no taper (scenario bonus_flat)")
    bonus_solve_start: float = _p(10_000, "Modelling choice", "judgement", "First upper bracket for the bonus_max bisection (doubled until it brackets the target)")
    bonus_solve_tol: float = _p(0.01, "Modelling choice", "judgement", "Bisection stops when the bracket is narrower than this ($)")

    # --- Budget neutrality search ---
    weights_file: str = _p("inputs/weights.csv",
                           "ASFA 2026 Table 4 (ATO 2% sample, women aged 65 to 69 with super, June 2024); Update 2",
                           "evidence",
                           "Population weight per balance member = share of women 65 to 69 with super in each balance "
                           "band (interpolated between published percentiles; $1m band extrapolated beyond p90)")
    weights: tuple = _p(None, "Modelling switch", "judgement",
                        "None = read weights_file; or ((balance, weight), ...) to override (used by choose_neutral_settings)")
    neutrality_primary: str = _p("all_purchasers", UPDATE1, "judgement",
                                 "Primary budget neutrality definition; cohort only is reported as secondary")
    grid_cap: tuple = _p((100_000, 400_000, 25_000), "Brief", "judgement", "(start, stop, step) of cap grid")
    grid_inc_pct: tuple = _p((0.30, 0.60, 0.05), "Brief", "judgement", "(start, stop, step) of inc_pct_in grid")
    fine_cap: tuple = _p((50_000, 12_500), UPDATE1, "judgement",
                         "(half width, step) of the fine cap grid around the chosen cap: $250k to $350k")
    fine_inc_pct: tuple = _p((0.05, 0.025), UPDATE1, "judgement",
                             "(half width, step) of the fine inc_pct_in grid around the chosen rate: 30% to 40%")
    neutrality_tolerance: float = _p(0.02, "Brief", "judgement", "Within 2% of current settings weighted cost")
    n_best: int = _p(5, "Modelling choice", "judgement", "Number of closest-to-neutral combinations shown in the gains shift table")

    # --- Sensitivity ---
    sens_real_return: tuple = _p((0.0, 0.03, 0.06), "Brief", "judgement", "")
    sens_allocation: tuple = _p((0.30, 0.50), "Brief", "judgement", "")
    sens_discount: tuple = _p((0.01, 0.03), "Brief", "judgement", "")
    sens_air: tuple = _p((0.01, 0.03), "Brief", "judgement", "")

    # --- Fiscal scale up ---
    count_source: str = _p("derived", UPDATE2, "judgement",
                           "'direct' = cohort_counts_file; 'derived' = women turning 67 x band share x single share "
                           "x homeowner share from cohort_inputs_file")
    cohort_counts_file: str = _p("inputs/cohort_counts.csv", "PLACEHOLDER counts, to be replaced with ATO/ABS numbers", "placeholder",
                                 "Direct counts; not used while count_source = 'derived'")
    cohort_inputs_file: str = _p("inputs/cohort_inputs.csv",
                                 "ASFA 2026 Tables 1 and 4; ABS 2021 Census G06; ABS Housing Occupancy and Costs 2019-20 "
                                 "Table 6.1 (Update 3). Each input's source is in its own column of the file",
                                 "evidence", "Inputs for count_source = 'derived' (rows also listed in this sheet)")
    placeholder_count: int = _p(1_000, "PLACEHOLDER", "placeholder", "Count per balance member per year written to the placeholder cohort file")
    placeholder_cohort_inputs: tuple = _p((100_000, 0.04, 0.5, 0.5), "PLACEHOLDER", "placeholder",
                                          "(women turning 67, share in band, single share, homeowner share) written to the "
                                          "placeholder cohort inputs file; chosen only so derived counts equal placeholder_count")
    scale_up_years: int = _p(10, "Brief", "judgement", "Number of entry years")
    take_up_rates: tuple = _p((0.05, 0.10, 0.20), "Brief", "judgement", "Take-up scenarios (baseline u0 for break even)")
    sens_homeowner_share: tuple = _p((0.717, 0.767), UPDATE3, "judgement",
                                     "Homeowner shares tested in the fiscal scale up only (10 and 5 points below the "
                                     "file value), as single older women likely own less often than all households 65 to 74")
    take_up_step: float = _p(0.01, UPDATE1, "judgement", "Extra take-up used for the marginal fiscal cost (1 percentage point)")
    options_take_up: float = _p(0.10, UPDATE1, "judgement", "Take-up used in options_summary (10 year total, break even u0)")
    options_iris_balance: int = _p(650_000, UPDATE1, "judgement", "Member used for the accumulation IRIS gap in options_summary")

    # --- Charts ---
    chart_dpi: int = _p(300, "Brief (overrides 150 dpi in ft_style_graph.md)", "judgement", "PNG resolution")
    chart_member: int = _p(500_000, "Brief", "judgement", "Member shown in the Age Pension by age chart")

    # --- Derived values ---
    @property
    def max_rate(self):
        """Maximum Age Pension, $ a year."""
        return self.max_rate_fn * self.fortnights

    @property
    def assets_taper(self):
        """Pension reduction, $ a year per $1 of assets over the free area."""
        return self.assets_taper_fn_per_1000 * self.fortnights / 1000

    @property
    def income_free_area(self):
        """Income test free area, $ a year."""
        return self.income_free_area_fn * self.fortnights

    @property
    def balances(self):
        return tuple(self.cohort_balances) + tuple(self.higher_balances)

    def with_(self, **changes):
        """Copy with some parameters changed (used for sensitivity tests)."""
        return replace(self, **changes)


BASE = Params()


def parameter_table(p: Params = BASE) -> pd.DataFrame:
    """Parameters with value, source and evidence/judgement/placeholder label."""
    rows = []
    for f in fields(p):
        value = getattr(p, f.name)
        rows.append({
            "parameter": f.name,
            "value": f"None (read from {p.weights_file})" if f.name == "weights" and value is None else str(value),
            "description": f.metadata["note"],
            "source": f.metadata["source"],
            "label": f.metadata["label"],
        })
    return pd.DataFrame(rows)
