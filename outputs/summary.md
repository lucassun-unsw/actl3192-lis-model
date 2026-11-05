# LIS model: final results (ACTL3192 Group 23)

Single female homeowners retiring at 67 with $400,000 to $650,000 in super (the cohort), plus $800,000 and $1m members to show who pays. All amounts are in today's dollars. Present values (PV) are survival weighted from 67 with ABS 2022-24 female mortality and a 2% real discount rate. Full tables are in `results.xlsx` (one sheet per table, a note in row 1) and the CSV files; charts are `chart1` to `chart7`.

## Final policy

**Retargeted LIS means test: cap $300,000 (real) on the purchase amount that gets concessional treatment; inside the cap, 40% of payments count under the income test** (assets 60%, 30% from 84, as now). Above the cap the LIS is treated like an account-based pension. Accumulation purchases count at most 5 years of deeming growth.

## Headline findings

- **Budget neutral.** Across all purchasers (ASFA 2026 weights) the final policy costs +$188 per woman aged 65 to 69 with super vs current settings (+1.31%), within the 2% neutrality band.
- **The cohort gains, higher balances pay.** Change in PV Age Pension vs current settings: $400k +$21,094; $500k +$24,126; $650k +$7,108; $800k -$29,738; $1m -$41,380. Every cohort member is better off than under current settings.
- **A bonus giving the cohort the same help costs much more.** The equal support bonus ($42,949 up to $400,000, tapering to nil at $700,000) is new spending of $3,538 per woman 65 to 69 with super, against +$188 for retargeting, for the same $3,538 of help to the cohort. A flat $10,000 bonus (upper bound) costs $1,655 but gives the cohort only $1,191.
- **Fiscal cost.** Lifetime cost of 10 years of new retirees at 10% take-up, all purchasers, undiscounted: current settings $448.4m, retargeted $454.3m, equal support bonus $558.7m, flat bonus $500.0m.
- **Take-up.** For the same total cost as current settings at 10% take-up, retargeting supports 9.9% take-up, the equal support bonus 8.0% and the flat bonus 9.0%.
- **Accumulation purchases.** At $650k, buying the LIS 20 years early adds $25,030 of PV Age Pension under current rules and $21,085 under the final policy (5 year limit).
- **Members' income.** For the bonus, the Age Pension falls through the clawback even though the member's total income rises (at $400k: PV Age Pension -$13,589, PV retiree income +$31,709 vs current settings).

## How to read the numbers

- 'vs all ABP' = the scenario minus the same member keeping the whole balance in an account-based pension; 'vs current' = minus the same member under current settings (50% in a LIS at 67).
- Government cost = change in PV Age Pension, plus the bonus for the bonus options.
- 'Weighted' = sum over members of population weight x value. The weights are the share of women aged 65 to 69 with super in each balance band and add to 0.288, so a weighted figure is per woman aged 65 to 69 with super (counting only the five modelled bands).
- Fiscal totals are the **lifetime** cost of everyone retiring in entry years 1 to 10, not cash spent inside a 10 year window; discounted totals use 1/(1 + 2%)^(t - 1) for entry year t.

## Options assessment

| option | fiscal d gov cost vs current weighted all | fiscal 10y lifetime cost 10% undiscounted | fiscal 10y lifetime cost 10% discounted | fiscal 10y vs current 10% undiscounted | income d pv income vs current weighted cohort | income d pv income vs current weighted all | equity age pension only d pv vs all abp 400k | equity age pension only d pv vs all abp 500k | equity age pension only d pv vs all abp 650k | equity retiree income d pv vs current 400k | equity retiree income d pv vs current 500k | equity retiree income d pv vs current 650k | equity iris gap 650k | take up break even u0 10% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Current settings | 0 | 448.4 | 410.8 | 0.0 | 0 | 0 | -10,303 | 24,874 | 83,758 | 0 | 0 | 0 | 25,030 | 10.0% |
| Retargeted | 188 | 454.3 | 416.2 | 5.9 | 3,538 | 188 | 10,791 | 49,000 | 90,867 | 21,094 | 24,126 | 7,108 | 21,085 | 9.9% |
| Bonus, equal support | 3,538 | 558.7 | 511.9 | 110.3 | 3,833 | 3,833 | -23,892 | 14,766 | 80,025 | 31,709 | 20,091 | 3,816 | 25,030 | 8.0% |
| Bonus, flat $10,000 | 1,655 | 500.0 | 458.1 | 51.6 | 1,297 | 1,813 | -13,467 | 21,408 | 78,542 | 7,383 | 7,081 | 5,331 | 25,030 | 9.0% |
| Deferred annuity |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

10 year columns in $ million; other money columns in $ (weighted columns per woman 65 to 69 with super). Equity: 'age pension only' = change in PV Age Pension vs all ABP (government spending on the member, not the member's whole outcome); 'retiree income' = change in PV of drawdowns + LIS payments + Age Pension vs current settings. The IRIS gap for the bonus options is the current rules gap, as the bonus keeps current means test rules. Simplicity and risk are left for the group to score (High / Medium / Low) in the `options_summary` sheet. Deferred annuity: considered, not modelled.

## Results by member

Changes vs all ABP. `bonus` = equal support bonus, `bonus_flat` = flat bonus upper bound, `*_accum` / `accum_iris` = LIS bought 20 years before 67. `cost_per_extra_dollar_gov` = government cost / change in PV income.

| scenario | balance | lis_purchase | bonus | age_pension_67 | binding_test_67 | d_pv_age_pension | d_pv_income | d_pv_bequest | gov_cost | cost_per_extra_dollar_gov |
|---|---|---|---|---|---|---|---|---|---|---|
| current_lis | 400,000 | 200,000 | 0 | 28,723 | income | -10,303 | 42,509 | -65,905 | -10,303 | -0.24 |
| accum_iris | 400,000 | 200,000 | 0 | 28,723 | income | -10,303 | 42,509 | -65,905 | -10,303 | -0.24 |
| retargeted | 400,000 | 200,000 | 0 | 29,828 | income | 10,791 | 63,603 | -65,905 | 10,791 | 0.17 |
| retargeted_accum | 400,000 | 200,000 | 0 | 29,828 | income | 10,791 | 63,603 | -65,905 | 10,791 | 0.17 |
| bonus | 400,000 | 242,949 | 42,949 | 28,012 | income | -23,892 | 74,218 | -65,905 | 19,056 | 0.26 |
| bonus_flat | 400,000 | 210,000 | 10,000 | 28,558 | income | -13,467 | 49,892 | -65,905 | -3,467 | -0.07 |
| current_lis | 500,000 | 250,000 | 0 | 26,954 | assets | 24,874 | 90,889 | -82,382 | 24,874 | 0.27 |
| accum_iris | 500,000 | 250,000 | 0 | 26,957 | income | 24,877 | 90,892 | -82,382 | 24,877 | 0.27 |
| retargeted | 500,000 | 250,000 | 0 | 26,954 | assets | 49,000 | 115,015 | -82,382 | 49,000 | 0.43 |
| retargeted_accum | 500,000 | 250,000 | 0 | 27,931 | assets | 50,838 | 116,853 | -82,382 | 50,838 | 0.44 |
| bonus | 500,000 | 278,632 | 28,632 | 25,614 | assets | 14,766 | 110,980 | -82,382 | 43,399 | 0.39 |
| bonus_flat | 500,000 | 260,000 | 10,000 | 26,486 | assets | 21,408 | 97,970 | -82,382 | 31,408 | 0.32 |
| current_lis | 650,000 | 325,000 | 0 | 17,594 | assets | 83,758 | 169,578 | -107,096 | 83,758 | 0.49 |
| accum_iris | 650,000 | 325,000 | 0 | 22,072 | assets | 108,789 | 194,608 | -107,096 | 108,789 | 0.56 |
| retargeted | 650,000 | 325,000 | 0 | 16,814 | assets | 90,867 | 176,686 | -107,096 | 90,867 | 0.51 |
| retargeted_accum | 650,000 | 325,000 | 0 | 18,864 | assets | 111,952 | 197,772 | -107,096 | 111,952 | 0.57 |
| bonus | 650,000 | 332,158 | 7,158 | 17,259 | assets | 80,025 | 173,394 | -107,096 | 87,183 | 0.50 |
| bonus_flat | 650,000 | 335,000 | 10,000 | 17,126 | assets | 78,542 | 174,909 | -107,096 | 88,542 | 0.51 |
| current_lis | 800,000 | 400,000 | 0 | 8,234 | assets | 118,681 | 224,305 | -131,811 | 118,681 | 0.53 |
| accum_iris | 800,000 | 400,000 | 0 | 13,746 | assets | 168,477 | 274,101 | -131,811 | 168,477 | 0.61 |
| retargeted | 800,000 | 400,000 | 0 | 5,114 | assets | 88,944 | 194,568 | -131,811 | 88,944 | 0.46 |
| retargeted_accum | 800,000 | 400,000 | 0 | 7,719 | assets | 119,757 | 225,381 | -131,811 | 119,757 | 0.53 |
| bonus | 800,000 | 400,000 | 0 | 8,234 | assets | 118,681 | 224,305 | -131,811 | 118,681 | 0.53 |
| bonus_flat | 800,000 | 410,000 | 10,000 | 7,766 | assets | 112,856 | 229,027 | -131,811 | 122,856 | 0.54 |
| current_lis | 1,000,000 | 500,000 | 0 | 0 | nil | 67,090 | 199,120 | -164,764 | 67,090 | 0.34 |
| accum_iris | 1,000,000 | 500,000 | 0 | 2,644 | assets | 134,036 | 266,066 | -164,764 | 134,036 | 0.50 |
| retargeted | 1,000,000 | 500,000 | 0 | 0 | nil | 25,709 | 157,740 | -164,764 | 25,709 | 0.16 |
| retargeted_accum | 1,000,000 | 500,000 | 0 | 0 | nil | 45,643 | 177,673 | -164,764 | 45,643 | 0.26 |
| bonus | 1,000,000 | 500,000 | 0 | 0 | nil | 67,090 | 199,120 | -164,764 | 67,090 | 0.34 |
| bonus_flat | 1,000,000 | 510,000 | 10,000 | 0 | nil | 62,771 | 205,348 | -164,764 | 72,771 | 0.35 |

Means test binding at 67 (full year by year counts in `binding_tests`):

| scenario | $400k | $500k | $650k | $800k | $1m |
|---|---|---|---|---|---|
| all_abp | assets | assets | assets | nil | nil |
| current_lis | income | assets | assets | assets | nil |
| accum_iris | income | income | assets | assets | assets |
| retargeted | income | assets | assets | assets | nil |
| retargeted_accum | income | assets | assets | assets | nil |
| bonus | income | assets | assets | assets | nil |
| bonus_flat | income | assets | assets | assets | nil |

### Outcomes by age of death (undiscounted, vs all ABP)

| scenario | balance | death_age | extra_income | d_bequest | net_to_estate_and_member |
|---|---|---|---|---|---|
| current_lis | 400,000 | 75 | 20,090 | -168,080 | -147,990 |
| current_lis | 400,000 | 90 | 52,287 | -83,433 | -31,146 |
| current_lis | 400,000 | 100 | 108,574 | -29,454 | 79,120 |
| retargeted | 400,000 | 75 | 29,234 | -168,080 | -138,846 |
| retargeted | 400,000 | 90 | 80,623 | -83,433 | -2,809 |
| retargeted | 400,000 | 100 | 151,358 | -29,454 | 121,903 |
| bonus | 400,000 | 75 | 33,835 | -168,080 | -134,245 |
| bonus | 400,000 | 90 | 94,882 | -83,433 | 11,450 |
| bonus | 400,000 | 100 | 172,887 | -29,454 | 143,432 |
| current_lis | 500,000 | 75 | 62,980 | -210,100 | -147,120 |
| current_lis | 500,000 | 90 | 108,300 | -104,291 | 4,009 |
| current_lis | 500,000 | 100 | 170,907 | -36,818 | 134,089 |
| retargeted | 500,000 | 75 | 72,141 | -210,100 | -137,959 |
| retargeted | 500,000 | 90 | 141,452 | -104,291 | 37,161 |
| retargeted | 500,000 | 100 | 222,118 | -36,818 | 185,300 |
| bonus | 500,000 | 75 | 71,090 | -210,100 | -139,010 |
| bonus | 500,000 | 90 | 135,644 | -104,291 | 31,354 |
| bonus | 500,000 | 100 | 212,729 | -36,818 | 175,911 |
| current_lis | 650,000 | 75 | 104,354 | -273,130 | -168,776 |
| current_lis | 650,000 | 90 | 210,437 | -135,578 | 74,859 |
| current_lis | 650,000 | 100 | 284,792 | -47,863 | 236,929 |
| retargeted | 650,000 | 75 | 98,622 | -273,130 | -174,509 |
| retargeted | 650,000 | 90 | 223,899 | -135,578 | 88,321 |
| retargeted | 650,000 | 100 | 316,314 | -47,863 | 268,451 |
| bonus | 650,000 | 75 | 105,165 | -273,130 | -167,965 |
| bonus | 650,000 | 90 | 215,909 | -135,578 | 80,331 |
| bonus | 650,000 | 100 | 293,884 | -47,863 | 246,021 |
| current_lis | 800,000 | 75 | 119,388 | -336,160 | -216,773 |
| current_lis | 800,000 | 90 | 293,275 | -166,865 | 126,410 |
| current_lis | 800,000 | 100 | 381,280 | -58,909 | 322,371 |
| retargeted | 800,000 | 75 | 96,458 | -336,160 | -239,703 |
| retargeted | 800,000 | 90 | 258,086 | -166,865 | 91,221 |
| retargeted | 800,000 | 100 | 353,315 | -58,909 | 294,406 |
| bonus | 800,000 | 75 | 119,388 | -336,160 | -216,773 |
| bonus | 800,000 | 90 | 293,275 | -166,865 | 126,410 |
| bonus | 800,000 | 100 | 381,280 | -58,909 | 322,371 |
| current_lis | 1,000,000 | 75 | 55,424 | -420,201 | -364,777 |
| current_lis | 1,000,000 | 90 | 293,220 | -208,582 | 84,639 |
| current_lis | 1,000,000 | 100 | 403,509 | -73,636 | 329,873 |
| retargeted | 1,000,000 | 75 | 43,016 | -420,201 | -377,185 |
| retargeted | 1,000,000 | 90 | 234,961 | -208,582 | 26,380 |
| retargeted | 1,000,000 | 100 | 338,026 | -73,636 | 264,390 |
| bonus | 1,000,000 | 75 | 55,424 | -420,201 | -364,777 |
| bonus | 1,000,000 | 90 | 293,220 | -208,582 | 84,639 |
| bonus | 1,000,000 | 100 | 403,509 | -73,636 | 329,873 |

## Budget neutrality (all purchasers)

Current settings weighted cost: $14,384 per woman 65 to 69 with super. Grid: cap $100,000 to $400,000 step $25,000; income test share 30% to 60% step 5%. Settings within 2% of current settings (heatmap: chart 4):

| cap | inc_pct_in | weighted_cost | difference | pct_difference |
|---|---|---|---|---|
| 275,000 | 35% | 14,309 | -75 | -0.5% |
| 350,000 | 50% | 14,262 | -122 | -0.8% |
| 400,000 | 55% | 14,510 | 126 | +0.9% |
| 300,000 | 40% | 14,572 | 188 | +1.3% |

Fine grid around the final policy (cap $250,000 to $350,000, 35% to 45%), five closest to neutral:

| rank | cap | inc_pct_in | difference | pct_difference | within_tolerance | final_policy |
|---|---|---|---|---|---|---|
| 1 | 287,500 | 37.5% | 65 | +0.5% | True | False |
| 2 | 275,000 | 35% | -75 | -0.5% | True | False |
| 3 | 300,000 | 40% | 188 | +1.3% | True | True |
| 4 | 312,500 | 42.5% | 273 | +1.9% | True | False |
| 5 | 312,500 | 45% | -328 | -2.3% | False | False |

The closest combination, cap $287,500 / 37.5% (+0.45%), is shown for reference; the group chose cap $300,000 / 40%. How the final policy moves Age Pension between members (retargeted minus current, per member; retiree income moves by the same amount, as only the Age Pension changes):

| balance | d_pv_ap_current | d_pv_ap_retargeted | shift_pv_ap |
|---|---|---|---|
| 400,000 | -10,303 | 10,791 | 21,094 |
| 500,000 | 24,874 | 49,000 | 24,126 |
| 650,000 | 83,758 | 90,867 | 7,108 |
| 800,000 | 118,681 | 88,944 | -29,738 |
| 1,000,000 | 67,090 | 25,709 | -41,380 |

Secondary definition, cohort only: current settings weighted cost $5,486; full grid in `neutrality_cohort_secondary`.

## Equal support bonus

Equal total cost would set the bonus to zero, because retargeting is budget neutral. Instead the bonus is sized to give the cohort the same help: the weighted change in government cost for the cohort under retargeting is $3,538; keeping the taper, bisection gives bonus_max = **$42,949** (chart 6).

| policy | bonus_max | cohort_d_gov_cost_vs_current | all_d_gov_cost_vs_current | cohort_income_per_1_cost_vs_current | all_income_per_1_cost_vs_current | cohort_income_per_1_cost_vs_all_abp | all_income_per_1_cost_vs_all_abp |
|---|---|---|---|---|---|---|---|
| current_lis | 0 | 0 | 0 | n/a | n/a | 3.35 | 2.68 |
| retargeted | 0 | 3,538 | 188 | 1.00 | n/a | 2.43 | 2.65 |
| bonus | 42,949 | 3,538 | 3,538 | 1.08 | 1.08 | 2.46 | 2.36 |
| bonus_flat | 10,000 | 1,191 | 1,655 | 1.09 | 1.10 | 2.95 | 2.51 |

'income per $1 of cost vs current' = extra PV retiree income / extra government cost relative to current settings (n/a where the cost change is about zero); 'vs all ABP' = PV income gained / total government cost of the LIS. The bonus gives a little more than $1 of income per $1 of cost because the extra LIS payments are priced at the 2% AIR but rise with R = 3%, which outweighs the 5% loading.

**Clawback.** The bonus raises the LIS purchase amount and payments. For income test members (at 67: $400k) the extra payments reduce the Age Pension; for assets test members the larger assessed purchase amount does. Part of each bonus dollar comes back as lower Age Pension:

| policy | balance | binding_test_67_bonus | bonus | clawback | clawback_share_of_bonus | net_gov_cost_vs_current | d_pv_income_vs_current |
|---|---|---|---|---|---|---|---|
| bonus | 400,000 | income | 42,949 | 13,589 | 32% | 29,359 | 31,709 |
| bonus | 500,000 | assets | 28,632 | 10,108 | 35% | 18,525 | 20,091 |
| bonus | 650,000 | assets | 7,158 | 3,734 | 52% | 3,424 | 3,816 |
| bonus_flat | 400,000 | income | 10,000 | 3,164 | 32% | 6,836 | 7,383 |
| bonus_flat | 500,000 | assets | 10,000 | 3,466 | 35% | 6,534 | 7,081 |
| bonus_flat | 650,000 | assets | 10,000 | 5,216 | 52% | 4,784 | 5,331 |
| bonus_flat | 800,000 | assets | 10,000 | 5,825 | 58% | 4,175 | 4,722 |
| bonus_flat | 1,000,000 | nil | 10,000 | 4,319 | 43% | 5,681 | 6,228 |

## Accumulation IRIS limit

Gap = extra PV Age Pension from buying the LIS 20 years before 67 instead of at 67. Under current rules the recorded purchase amount grows at the 3.75% deeming rate, below actual growth, so buying early lowers the assessed asset. The final policy counts at most 5 years of deeming growth (20 = no limit; chart 7):

| balance | iris_years_cap | gap_retargeted | gap_current |
|---|---|---|---|
| 400,000 | 0 | 0 | 0 |
| 400,000 | 5 | 0 | 0 |
| 400,000 | 10 | 0 | 0 |
| 400,000 | 20 | 0 | 0 |
| 500,000 | 0 | 0 | 3 |
| 500,000 | 5 | 1,838 | 3 |
| 500,000 | 10 | 2,245 | 3 |
| 500,000 | 20 | 2,245 | 3 |
| 650,000 | 0 | 0 | 25,030 |
| 650,000 | 5 | 21,085 | 25,030 |
| 650,000 | 10 | 30,045 | 25,030 |
| 650,000 | 20 | 43,525 | 25,030 |
| 800,000 | 0 | 0 | 49,796 |
| 800,000 | 5 | 30,813 | 49,796 |
| 800,000 | 10 | 58,762 | 49,796 |
| 800,000 | 20 | 99,547 | 49,796 |
| 1,000,000 | 0 | 0 | 66,946 |
| 1,000,000 | 5 | 19,934 | 66,946 |
| 1,000,000 | 10 | 43,291 | 66,946 |
| 1,000,000 | 20 | 99,093 | 66,946 |

## Fiscal cost: lifetime cost of 10 years of new retirees ($ million)

New single homeowner retirees a year across the five members: 8,984. All purchasers:

| scenario | take_up | purchasers | lifetime_cost_undiscounted | lifetime_cost_discounted |
|---|---|---|---|---|
| current_lis | 5% | 4,492 | 224.2 | 205.4 |
| current_lis | 10% | 8,984 | 448.4 | 410.8 |
| current_lis | 20% | 17,968 | 896.8 | 821.7 |
| retargeted | 5% | 4,492 | 227.1 | 208.1 |
| retargeted | 10% | 8,984 | 454.3 | 416.2 |
| retargeted | 20% | 17,968 | 908.5 | 832.4 |
| bonus | 5% | 4,492 | 279.3 | 255.9 |
| bonus | 10% | 8,984 | 558.7 | 511.9 |
| bonus | 20% | 17,968 | 1,117.4 | 1,023.8 |
| bonus_flat | 5% | 4,492 | 250.0 | 229.1 |
| bonus_flat | 10% | 8,984 | 500.0 | 458.1 |
| bonus_flat | 20% | 17,968 | 1,000.0 | 916.2 |

Homeowner share sensitivity (base 0.817; single older women are likely to own less often than all households aged 65 to 74). Totals scale in proportion; $ million, all purchasers:

| scenario | take_up | undiscounted at 0.717 | undiscounted at 0.767 | undiscounted at 0.817 | discounted at 0.717 | discounted at 0.767 | discounted at 0.817 |
|---|---|---|---|---|---|---|---|
| current_lis | 5% | 196.8 | 210.5 | 224.2 | 180.3 | 192.8 | 205.4 |
| current_lis | 10% | 393.5 | 421.0 | 448.4 | 360.5 | 385.7 | 410.8 |
| current_lis | 20% | 787.0 | 841.9 | 896.8 | 721.1 | 771.4 | 821.7 |
| retargeted | 5% | 199.3 | 213.2 | 227.1 | 182.6 | 195.4 | 208.1 |
| retargeted | 10% | 398.7 | 426.5 | 454.3 | 365.3 | 390.7 | 416.2 |
| retargeted | 20% | 797.3 | 852.9 | 908.5 | 730.5 | 781.5 | 832.4 |
| bonus | 5% | 245.2 | 262.2 | 279.3 | 224.6 | 240.3 | 255.9 |
| bonus | 10% | 490.3 | 524.5 | 558.7 | 449.2 | 480.6 | 511.9 |
| bonus | 20% | 980.6 | 1,049.0 | 1,117.4 | 898.5 | 961.1 | 1,023.8 |
| bonus_flat | 5% | 219.4 | 234.7 | 250.0 | 201.0 | 215.0 | 229.1 |
| bonus_flat | 10% | 438.8 | 469.4 | 500.0 | 402.0 | 430.1 | 458.1 |
| bonus_flat | 20% | 877.6 | 938.8 | 1,000.0 | 804.1 | 860.2 | 916.2 |

## Take-up break even (all purchasers)

Break even take-up u* = u0 x (cost per buyer, current settings) / (cost per buyer, policy): the take-up the policy can reach for the same total cost as current settings at take-up u0 (above u0 = cheaper per buyer). 'not binding' would mean the policy's cost per buyer is zero or negative. Extra cost of one more point of take-up = 1% x lifetime cost of all new retirees under the policy ($ million).

| policy | u0 | cost_per_buyer_current | cost_per_buyer_policy | break_even_take_up | extra_cost_per_1pt_take_up | extra_cost_per_1pt_take_up_discounted |
|---|---|---|---|---|---|---|
| retargeted | 5% | 49,910 | 50,562 | 4.9% | 45.4 | 41.6 |
| retargeted | 10% | 49,910 | 50,562 | 9.9% | 45.4 | 41.6 |
| retargeted | 20% | 49,910 | 50,562 | 19.7% | 45.4 | 41.6 |
| bonus | 5% | 49,910 | 62,186 | 4.0% | 55.9 | 51.2 |
| bonus | 10% | 49,910 | 62,186 | 8.0% | 55.9 | 51.2 |
| bonus | 20% | 49,910 | 62,186 | 16.1% | 55.9 | 51.2 |
| bonus_flat | 5% | 49,910 | 55,654 | 4.5% | 50.0 | 45.8 |
| bonus_flat | 10% | 49,910 | 55,654 | 9.0% | 50.0 | 45.8 |
| bonus_flat | 20% | 49,910 | 55,654 | 17.9% | 50.0 | 45.8 |

## Data and assumptions

Evidence based: Services Australia Age Pension and deeming rates from 20 September 2026; DSS LIS means test rules; minimum drawdown rates; ABS Life Tables 2022-24 (females).

Judgement: real return 3% (ABP and LIS), inflation 2.5%, AIR 2%, loading 5%, 50% of the balance in the LIS, real discount rate 2%; Age Pension settings constant in real terms.

Population and counts:
- Weights: ASFA 2026 Table 4 (ATO 2% sample, women 65 to 69 with super, June 2024): $400k 0.0707, $500k 0.0690, $650k 0.0537, $800k 0.0492, $1m 0.0456.
- New retirees a year = women reaching 67 with super (99,106; ASFA 2026 Table 1) x band share (as the weights) x single share (0.385; ABS 2021 Census G06) x homeowner share (0.817; ABS HOC 2019-20 Table 6.1).

Every parameter, input value and source is in the `parameters` sheet.

### Limitations

- Balances are for all women aged 65 to 69 with super, not only single homeowners at 67.
- Band shares are interpolated between the published percentiles (ASFA 2026 Table 4); the $1m band is extrapolated beyond the 90th percentile.
- The single share uses ages 65 to 74, not 67 exactly.
- The homeowner share is for all households with a reference person aged 65 to 74, not single women; single older women are likely to own less often, hence the 0.717 and 0.767 sensitivity.
- Census 2021 and HOC 2019-20 are older than the June 2024 super data.
- Counts assume single homeowners have the same balance distribution as all women aged 65 to 69 with super.
- Members are stylised: everyone in a band is modelled at the band's single balance.

### Modelling choices

1. **Core logic copied from the Excel model.** Drawdowns and LIS payments at the start of each year; LIS priced as a life annuity due at the AIR using the same ABS mortality; payments then move with (1 + R) / (1 + AIR); the LIS purchase amount is fixed in nominal terms, so its assessed value shrinks by inflation (2.5%) each year in today's dollars. Life table ends at 100; anyone alive at 100 is treated as dying during that year.
2. **Accumulation IRIS (scenario 3).** The LIS value at 67 equals the same 50% allocation, so payments are identical to current settings; only the assessed purchase amount differs. Recorded / actual = ((1 + 3.75%) / ((1 + 2.5%)(1 + R)))^20 = 0.706 at R = 3% (deeming growth is lower than actual nominal growth), so the assessed asset is smaller and the member receives more Age Pension. The threshold age stays 84 (later of 84 and 5 years after purchase).
3. **Retargeted policy above the cap (group decision).** The recorded purchase amount is split once, at 67: inside = min(purchase, cap $300,000), above = the rest. Inside: assets 60% (30% from 84), income 40% of the related payments. Above: 100% of the amount counts as an asset and 100% of the related payments as income. Both parts are deflated by inflation each year, as under current rules. Payments are split in the same proportion as the purchase amount.
4. **Retargeted policy for an accumulation purchase (group decision).** Scenario `retargeted_accum`. Deeming growth is counted for min(20, iris_years_cap = 5) years; the cap is applied to the recorded (deeming grown) amount. Used in the IRIS cap sensitivity, chart 7 and the options summary; the sensitivity tests, neutrality search and other charts use the purchase at 67.
5. **Equal support bonus.** Bonus based on the balance at 67 before the bonus, added to the LIS purchase, so it is reduced by the product loading and assessed under both tests as part of the purchase; the ABP part is unchanged. Government cost = bonus + change in PV Age Pension. bonus_max is solved by bisection to within $0.01 (22 steps) so the weighted cohort change in government cost vs current settings equals that of the retargeted policy. The solve is done once at base inputs; the sensitivity tests hold this bonus_max fixed (a dollar bonus would not be re-set when returns change).
6. **Retiree income per $1 of government cost** is shown two ways: relative to current settings (extra income / extra cost; n/a for a budget neutral policy, whose extra cost is about zero; for retargeting it is 1.00 whenever defined, because only the Age Pension changes) and relative to all ABP (total). Government cost per extra $1 of income in `base_results` is n/a where retiree income does not rise.
7. **Budget neutrality.** Weighted cost = sum of weight x change in PV Age Pension (weights in `inputs/weights.csv`); the 2% band is relative to the current settings weighted cost of the same member group. 'Closest' combinations exclude those that reproduce current settings exactly. All 'weighted' figures elsewhere are weighted sums with the same weights.
8. **Sensitivity (group decision).** One input changed at a time, others at base. Changing R also changes the all ABP comparison, so changes are always against all ABP under the same inputs.
9. **Fiscal scale up.** Cost per member is a lifetime PV at 67, so totals are the lifetime cost of 10 years of new retirees, not cash spent inside a 10 year window. Discounted totals discount entry year t by (1 + 2%)^(t - 1) (first cohort retires now). The same take-up rate is applied to every balance. Members are stylised: each count is assumed to have exactly that balance. Break even take-up and the marginal cost use the cohort counts (not the weights) so they match the fiscal totals.
10. **Options summary.** Fiscal and income columns are weighted sums vs current settings; 10 year totals at 10% take-up, all purchasers. Equity is shown two ways: change in PV Age Pension vs all ABP (Age Pension only) and change in PV retiree income vs current settings. The IRIS gap for the bonus options is the current rules gap, because the bonus keeps current means test rules (a bonus paid into an accumulation purchase is not modelled).
11. **Charts** follow ft_style_graph.md but are saved at 300 dpi as the brief asks, and use hatching, line styles and markers so they read in black and white. The heatmap uses the cividis colour map, whose lightness changes evenly, with values printed in every cell.

## Placeholders

None in use. (`inputs/cohort_counts.csv` keeps placeholder direct counts but is not used.)

## Model checks

All tests pass (34 passed in 1.30s). The model reproduces the group's Excel model: every reconciliation target within $5 and every projection cell of the Excel `Member_*` sheets within $0.000001. Model life expectancy at 67 is 87.90 (ABS 88.0; the table ends at 100). Other tests check the final policy settings and its neutrality, the equal support solve, the IRIS limit, the input data and the homeowner sensitivity.

Rerun everything with `python -m lis_model.run_all`.
