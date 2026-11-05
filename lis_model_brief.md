# LIS model specification (ACTL3192 Industry Project, Group 23)

This document sets out the assumptions, logic, scenarios and outputs of the model. See
[`README.md`](README.md) for a short overview and how to run it.

## Context
The model supports a policy report on how government could encourage voluntary take-up of lifetime
income streams (LIS) in Australian retirement. The cohort is single female homeowners retiring at 67
with $400,000 to $650,000 in super. The Python model reproduces the group's earlier Excel model
(`ACTL3192_early_model.xlsx`) exactly. It then extends it with more scenarios, a budget neutrality
search, sensitivity tests, a 10 year fiscal cost scale-up, policy comparisons and charts.

Modelling is kept proportionate and transparent. Every assumption is stated and labelled as
evidence based or judgement, and ranges are shown where evidence is weak. Where an input is missing,
the model uses a clearly labelled placeholder and lists it in `outputs/summary.md`.

## Input files
`Data/`:
- `ACTL3192_early_model.xlsx`: the original Excel model, used for the reconciliation targets.
- `3302055001DO001_20222024.xlsx`: ABS Life Tables 2022 to 2024, sheet `Table 9`. Age is in column A
  and female lx in column F. Data rows start at age 0 on row 8, and age 100 is the last row.

`inputs/` (see "Population weights and cohort counts"):
- `weights.csv`: population weight per balance member (columns `balance_member, weight, source`).
- `cohort_inputs.csv`: inputs for the derived cohort counts, one row per entry year and balance member
  (columns `year, balance_member, women_turning_67, share_in_band, single_share, homeowner_share`,
  and one source column per input: `women_source, band_source, single_source, homeowner_source`).
- `cohort_counts.csv`: the direct counts option (columns `year, balance_member, count`). It holds
  PLACEHOLDER counts (1,000 per member per year) and is only read if `count_source = "direct"`.

If an input file is missing, the model recreates it with clearly labelled PLACEHOLDER values.

## Project structure
```
lis_model/
  params.py          # all parameters in one dataclass, with source and evidence/judgement/placeholder label
  inputs.py          # read weights and cohort counts (direct or derived), write placeholder files if missing
  mortality.py       # load ABS female lx, tpx from 67, death probabilities
  means_test.py      # deeming, assets test, income test, Age Pension
  projection.py      # year by year projection for one member under one scenario
  scenarios.py       # scenario definitions (see below)
  metrics.py         # PVs, bequest, age of death outcomes, cost per extra $ of income
  search.py          # budget neutrality search, fine grid, choose_neutral_settings
  policies.py        # equal support bonus solve, bonus clawback, IRIS cap sensitivity, options summary
  sensitivity.py     # one-at-a-time sensitivity tests
  scale_up.py        # 10 year fiscal cost, homeowner share sensitivity, take-up break even
  charts.py          # matplotlib figures for the report
  run_all.py         # runs everything, writes outputs/
tests/
  test_reconcile.py  # matches the Excel model (targets below)
  test_policy.py     # final policy settings, neutrality, equal support solve, IRIS limit, break even
  test_inputs.py     # real weights and cohort inputs, homeowner share sensitivity
inputs/              # weights.csv, cohort_inputs.csv, cohort_counts.csv
outputs/             # CSV tables, results.xlsx, PNG charts, summary.md
requirements.txt     # numpy, pandas, openpyxl, matplotlib, pytest
```
All parameters live in `params.py`.

## Base parameters (20 September 2026 settings)
Evidence based:
- Maximum single Age Pension incl. supplements: $1,237.70 per fortnight, x 26 per year
- Assets test free area, single homeowner: $333,000; taper $3 per fortnight per $1,000 over (= 0.078 per $ per year)
- Income test free area: $226 per fortnight (x 26); taper 50 cents per $
- Deeming: 1.75% on first $66,800, 3.75% above
- LIS means test: 60% of the purchase amount is assessed under the assets test until threshold age 84,
  then 30%; 60% of gross payments are assessed as income
- Minimum drawdown by age at start of year: 65 to 74: 5%, 75 to 79: 6%, 80 to 84: 7%, 85 to 89: 9%, 90 to 94: 11%, 95+: 14%
- Mortality: ABS 2022 to 2024 female lx, ages 67 to 100

Judgement:
- Real net return R = 3% (ABP and LIS share the same portfolio)
- Inflation = 2.5% (only used to shrink the fixed nominal LIS purchase amount in real terms)
- LIS assumed investment return AIR = 2% real; product loading = 5%
- Allocation to LIS = 50% of balance at 67
- Real discount rate = 2%
- All Age Pension parameters held constant in real terms

## Projection logic (matches the Excel model)
Ages 67 to 100, t = 0..33, annual steps, all in real terms.
- tpx = lx(age) / lx(67). Probability of dying during year t = tpx(t) - tpx(t+1); for the last row (age 100) it is tpx(t).
- Discount factor v_t = 1 / (1 + disc)^t.
- Minimum drawdown taken at the START of each year from the opening ABP balance.
- ABP closing = (opening - drawdown) x (1 + R).
- LIS priced as a life annuity due at the AIR: factor = sum_t tpx(t) / (1 + AIR)^t;
  first payment = purchase x (1 - loading) / factor; payment_t = first payment x ((1 + R) / (1 + AIR))^t.
- LIS assessed assets_t = purchase / (1 + inflation)^t x (60% if age < 84 else 30%).
- Deemed income on ABP opening balance using the two tier deeming rates.
- Assessed income = deemed ABP income + 60% x LIS payment.
- Assets test pension = max(0, MAX - max(0, ABP opening + LIS assessed assets - free area) x 0.078).
- Income test pension = max(0, MAX - max(0, assessed income - income free area) x 0.5).
- Age Pension = min(assets test pension, income test pension), recording which test binds.
- Total income = drawdown + LIS payment + Age Pension.

Metrics per member per scenario:
- PV Age Pension = sum tpx x v_t x AP_t; PV income = sum tpx x v_t x total income_t
- PV expected bequest = sum (prob die in year t) x v_t x ABP closing_t / (1 + disc)
- Change vs the all ABP scenario for each of these
- Government cost = change in PV Age Pension, plus the bonus for the bonus scenarios
- Government cost per extra $1 of retiree income = government cost / change in PV income
- Age of death outcomes for death at 75, 90, 100 (undiscounted): extra income = sum over ages < D of
  (income with LIS - income all ABP); change in bequest = ABP opening balance at age D (LIS case minus all ABP)

## Reconciliation targets (from the Excel model, ABS mortality, base parameters)
`tests/test_reconcile.py` checks each value to within $5. Balances: $400k, $500k, $650k.
- Age Pension at 67, all ABP: 26,954 / 19,154 / 7,454
- Age Pension at 67, 50% LIS: 28,723 / 26,954 / 17,594
- Change in PV Age Pension: -10,303 / +24,874 / +83,758
- Change in PV retiree income: +42,509 / +90,889 / +169,578
- Change in PV expected bequest: -65,905 / -82,382 / -107,096
- Death at 75, change in bequest: -168,080 / -210,100 / -273,130
- Model life expectancy at 67 is about 87.9 (ABS gives 88.0; the gap comes from ending at 100)

The test also checks every projection cell of the Excel `Member_*` sheets.

## Scenarios
Members: $400k, $500k and $650k (the cohort), plus $800k and $1,000k (higher balances, used to show who pays).
1. `all_abp`: full balance in an account-based pension.
2. `current_lis`: current settings, 50% in a LIS at 67.
3. `accum_iris`: current settings, with the LIS bought during accumulation 20 years before retirement.
   The amount at 67 equals the same 50% allocation, but the recorded purchase amount for the assets
   test grows at the 3.75% upper deeming rate (nominal) instead of actual returns:
   recorded / actual = ((1 + 3.75%) / ((1 + inflation)(1 + R)))^years_held, years_held = 20 (parameter).
4. `retargeted`: proposed policy. **Final policy: cap $300,000 (real), inc_pct_in 40%**
   (`use_chosen_neutral = False`). All scenarios, charts, age of death results, sensitivity tests and
   the fiscal scale-up use these settings.
   - cap: concessional treatment applies only to the purchase amount up to the cap
   - inside the cap: assets are assessed at 60%/30% as now, and the income test counts `inc_pct_in`
     of payments
   - above the cap: treated like an ABP. Modelling choice: 100% of the real purchase amount above the
     cap counts as an asset and 100% of the related payments count as income
5. `retargeted_accum`: the retargeted policy for an accumulation purchase. Deeming growth is counted
   for at most `iris_years_cap` years (default 5).
6. `bonus`: alternative policy, the **equal support bonus** (used everywhere a bonus appears).
   The government pays a bonus into the LIS at purchase, with current means test rules otherwise.
   Bonus = bonus_max for balances up to $400,000, tapering linearly to 0 at $700,000. bonus_max is
   solved, not set (see "Equal support bonus comparison"). The bonus increases the purchase amount and
   is assessed as part of it. Government cost = bonus + change in PV Age Pension.
7. `bonus_flat`: a flat $10,000 bonus at every balance (no taper), with current rules otherwise, as an
   upper bound sensitivity.

## Budget neutrality search
Goal: retargeted policy settings that cost about the same as current settings.
- Weighted cost = sum over members of weight x (PV AP under policy - PV AP under all ABP), using the
  population weights in `inputs/weights.csv`.
- Primary definition: **all purchasers** ($400k, $500k, $650k, $800k, $1m). Cohort only
  ($400k to $650k) results are kept as a secondary table, clearly labelled secondary.
- Grid search: cap from $100,000 to $400,000 (step $25,000) and inc_pct_in from 30% to 60% (step 5%).
  Reports all combinations within 2% of the weighted cost of current settings, and how gains shift
  between members for the best combinations.
- Finer search around the chosen point: cap from $250,000 to $350,000 in $12,500 steps and inc_pct_in
  from 30% to 40% in 2.5% steps, all purchasers. Reports the five combinations closest to neutral and
  the gains shift table for each.
- `choose_neutral_settings(weights)` returns the combination closest to neutral (all purchasers), so it
  can be rerun in one step when the weights change. `summary.md` shows the settings used and the
  closest combination at the top, and warns if either is more than 2% from current settings. The
  closest combination is for reference only; the group fixed the final policy.

## Equal support bonus comparison
The retargeted policy is budget neutral, so "equal total cost" would set the bonus to zero. Instead,
the two policies are compared on **equal support to the cohort**:
- Target = weighted sum, over the cohort members ($400k, $500k, $650k), of the change in government
  cost under the retargeted policy compared with current settings (the money the retargeted policy
  moves to the cohort).
- The bonus keeps its taper shape (full bonus up to $400,000, tapering linearly to zero at $700,000).
  `bonus_max` is solved by bisection so the bonus gives the cohort the same weighted change in
  government cost.
- Reported: the solved bonus_max, the extra cost to government of the bonus across all purchasers
  (new spending), and the retiree income gained per $1 of government cost for each policy.
- The flat $10,000 bonus is run as a sensitivity case, labelled "upper bound".
- Clawback: for members bound by the income test, extra LIS payments reduce the Age Pension; for
  members bound by the assets test, the larger assessed purchase amount reduces it. The clawback is
  tabled by member.

## Accumulation IRIS limit
- `iris_years_cap = 5` is the default for `retargeted_accum`.
- Sensitivity table for `retargeted_accum` with iris_years_cap = 0, 5, 10 and 20 (20 = no limit, same
  as current rules) for every member. It shows d_pv_age_pension and the gap versus buying at 67
  (retargeted_accum minus retargeted, and accum_iris minus current_lis for comparison).

## Sensitivity tests
Scenarios all_abp, current_lis, retargeted and bonus are run for R = 0%, 3%, 6%; allocation 30% and
50%; discount rate 1% and 3%; and AIR 1% and 3%, one input at a time. bonus_max is held at its base
solve. Results are in one tidy table (long format).

## Population weights and cohort counts
Weights (`inputs/weights.csv`): the share of women aged 65 to 69 with super in each balance band, from
ASFA 2026 Table 4 (derived from the ATO 2% sample, June 2024): $400k 0.0707, $500k 0.0690, $650k
0.0537, $800k 0.0492, $1m 0.0456. They add to 0.288, so weighted sums are per woman aged 65 to 69 with
super.

Cohort counts use the derived option (`count_source = "derived"` in params):
count = women reaching 67 each year with super x share in balance band x single share x homeowner share,
each read from `inputs/cohort_inputs.csv`:
- women reaching 67 each year with super: 99,106
  (ASFA 2026 Table 1: 495,530 women aged 65 to 69 with super, divided by 5)
- balance band shares: as in weights.csv (ASFA 2026 Table 4)
- single share: 0.385
  (ABS 2021 Census General Community Profile, Australia, Table G06: females aged 65 to 74,
  "not married" 446,656 of 1,160,455; social marital status, so de facto couples count as couples)
- homeowner share: 0.817
  (ABS Housing Occupancy and Costs 2019-20, Table 6.1: total owners, household reference person aged 65 to 74)

Each source is recorded in the parameters sheet. The direct option (`count_source = "direct"`,
`inputs/cohort_counts.csv`) is kept and still holds PLACEHOLDER counts. Any output that depends on a
placeholder says so in its sheet (first row note) and in `summary.md`.

Data limitations (also listed in `summary.md`):
- balances are for all women aged 65 to 69, not only single homeowners at 67;
- band shares are interpolated between published percentiles; the $1m band is extrapolated beyond the
  90th percentile;
- the single share uses ages 65 to 74 (not 67 exactly);
- the homeowner share is for all households with a reference person aged 65 to 74, not single women;
- Census 2021 and HOC 2019-20 are older than the 2024 super data;
- counts assume single homeowners have the same balance distribution as all women aged 65 to 69.

## Fiscal cost scale-up
Lifetime cost of 10 years of new retirees = sum over entry years t = 1..10 of cost per member x new
retirees in cohort_t x take-up rate.
- Take-up scenarios: 5%, 10% and 20%, for current settings, retargeted, bonus and flat bonus.
- Totals are in today's dollars, undiscounted across entry years, and also discounted by
  (1 + 2%)^(t - 1).
- These are the **lifetime cost of 10 years of new retirees**, not cash spent inside a 10 year window.
- Homeowner share sensitivity, for the fiscal scale-up only: 0.717 and 0.767 (10 and 5 points lower),
  because single older women are likely to own their home less often than all households aged 65 to
  74. Fiscal totals are reported for 0.717, 0.767 and 0.817.

## Take-up: break even measures
For each policy (retargeted, bonus, flat bonus) and each baseline take-up u0 in {5%, 10%, 20%}, all purchasers:
- Break even take-up: u* = u0 x (cost per buyer under current settings) / (cost per buyer under the policy).
  This is the take-up the policy can support for the same total cost as current settings at u0.
  If the cost per buyer under the policy is zero or negative, it is reported as "not binding".
- Extra fiscal cost of each additional 1 percentage point of take-up under the policy.

## Options assessment table
Sheet `options_summary` has one row per option (current settings, retargeted, bonus equal support,
bonus flat $10,000, deferred annuity) and these columns:
- fiscal cost: all purchasers weighted change in government cost vs current, and the 10 year total at 10% take-up
- retiree income: weighted change in PV income vs current, cohort and all purchasers
- equity:
  - change in PV Age Pension for $400k, $500k and $650k, labelled as Age Pension only (vs all ABP);
  - change in PV retiree income vs current settings for $400k, $500k and $650k;
  - the accumulation IRIS gap at $650k
- take-up: break even take-up at u0 = 10%
- simplicity and risk: left for the group to score (High / Medium / Low)

The deferred annuity was considered but not modelled.

## Charts
PNG, 300 dpi, readable in black and white, styled with `ft_style/`.
1. Change in PV Age Pension by balance, current vs retargeted vs bonus (grouped bars)
2. Age Pension by age for the $500k member, all ABP vs current LIS vs retargeted (lines)
3. Gains and losses by age of death (75, 90, 100) for each balance (grouped bars), for current
   settings, retargeted and bonus
4. Budget neutrality heatmap: weighted cost difference over cap x inc_pct_in. All purchasers is the
   primary chart and cohort only is secondary; the final policy cell is labelled
5. Sensitivity: change in PV Age Pension at R = 0%, 3%, 6%
6. Equal support comparison: one group per policy (retargeted, equal support bonus, flat $10,000
   bonus) showing (a) the weighted change in government cost given to the cohort and (b) the weighted
   extra cost to government across all purchasers, both vs current settings ("same help to the
   cohort, different cost to government")
7. Accumulation IRIS gap by balance under iris_years_cap 0, 5, 10, 20

## Outputs
- `outputs/results.xlsx`, with one sheet per table, a note in row 1 and the table from row 2. Sheets
  include base results, age of death, binding tests, sensitivity, neutrality grid (primary), within 2%,
  gains shift, `neutrality_fine_grid`, fine grid gains shift, cohort secondary tables, chosen settings,
  `bonus_equal_support`, bonus by member, `iris_cap_sensitivity`, fiscal scale-up,
  `fiscal_homeowner_sensitivity`, `take_up_break_even`, `options_summary`, weights used, cohort counts
  used, life table, projections, and parameters with source and evidence/judgement/placeholder label
  (including each input file value and its source).
- CSV copies of each table (note on the first line, starting with `#`) and PNG charts.
- `outputs/summary.md`: the final policy settings and neutrality check, key numbers, which test binds
  for each member, data limitations, placeholders still in use, and the modelling choices made.
