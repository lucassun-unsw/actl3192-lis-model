# Lifetime income stream (LIS) policy model

A Python model built for the UNSW ACTL3192 Industry Project (Group 23). It looks at how government
could encourage voluntary take-up of lifetime income streams in Australian retirement. The model
focuses on single female homeowners retiring at 67 with $400,000 to $650,000 in super, and includes
$800,000 and $1m members to show who pays.

## What the model does

- Projects each member year by year from age 67 to 100 in real terms. It covers account-based pension
  drawdowns, LIS payments and the Age Pension under the assets test, the income test and deeming
  (20 September 2026 settings), using ABS 2022–24 female mortality.
- Compares scenarios: all account-based pension, current LIS rules, LIS bought during accumulation,
  a retargeted LIS means test (the group's final policy: cap $300,000, 40% of payments assessed as
  income), an equal support government bonus and a flat $10,000 bonus.
- Reports survival-weighted present values of Age Pension, retiree income and bequests, plus
  outcomes by age of death and the government cost per extra $1 of retiree income.
- Runs a budget neutrality grid search, an equal support bonus solve, the accumulation IRIS limit
  sensitivity, one-at-a-time sensitivity tests, a 10 year fiscal cost scale-up and take-up break-even
  measures.
- Reproduces the group's original Excel model exactly. `tests/test_reconcile.py` checks every value
  against it.

Each assumption is listed in `lis_model/params.py` with its source and a label: evidence based,
judgement or placeholder. The full specification is in [`lis_model_brief.md`](lis_model_brief.md).

## How to run it

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python -m lis_model.run_all     # runs everything and writes outputs/
pytest                          # reconciliation and policy tests
```

Run these from the project folder. The outputs are:

- `outputs/results.xlsx`: one sheet per table, with a note in row 1
- CSV copies of each table
- charts 1 to 7 as PNG files
- `outputs/summary.md`: headline results, modelling choices and data limitations

## Project layout

```
lis_model/   model code (params, mortality, means test, projection, scenarios, search, policies, ...)
tests/       reconciliation against the Excel model and policy checks
inputs/      population weights and cohort count inputs (with sources)
Data/        ABS life tables and the original Excel model
ft_style/    chart styling
outputs/     generated tables, charts and summary
```

## Data sources

- ABS Life Tables 2022–24 (Table 9, females)
- ASFA 2026 super balance tables, derived from the ATO 2% sample (June 2024)
- ABS 2021 Census (Table G06)
- ABS Housing Occupancy and Costs 2019–20 (Table 6.1)

See `outputs/summary.md` for the data limitations.

## AI acknowledgement

The code was written with help from Claude Code (Anthropic's AI coding assistant). The group set
the specification, assumptions and policy choices. We reviewed the results and checked them against
our original Excel model.

## Disclaimer

This is a student project for educational purposes only. It is not financial advice or an official
costing.
