"""ABS female life table: lx, survival from 67, and death probabilities."""

from functools import lru_cache

import numpy as np
import openpyxl
import pandas as pd

from .params import ROOT, Params


@lru_cache(maxsize=None)
def _read_lx(path, sheet, age_col, lx_col, first_row, max_age):
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)[sheet]
    last_row = first_row + max_age
    ages = [c.value for (c,) in ws[f"{age_col}{first_row}:{age_col}{last_row}"]]
    lx = [c.value for (c,) in ws[f"{lx_col}{first_row}:{lx_col}{last_row}"]]
    if ages != list(range(max_age + 1)):
        raise ValueError(f"Unexpected ages in {sheet}: {ages[:3]} ... {ages[-3:]}")
    return tuple(lx)


def load_lx(p: Params) -> pd.Series:
    """Female lx by age 0..max_age from ABS Table 9."""
    lx = _read_lx(str(ROOT / p.life_table_file), p.life_table_sheet, p.life_table_age_col,
                  p.life_table_lx_col, p.life_table_first_row, p.max_age)
    return pd.Series(lx, index=range(p.max_age + 1), name="lx", dtype=float)


def life_table(p: Params) -> pd.DataFrame:
    """Ages retirement_age..max_age with lx, tpx and probability of dying in each year.

    tpx = lx(age) / lx(67). Probability of dying during year t is tpx(t) - tpx(t+1),
    and tpx(t) for the last age, so the probabilities sum to 1.
    """
    lx = load_lx(p).loc[p.retirement_age:p.max_age]
    tpx = lx.to_numpy() / lx.iloc[0]
    q = tpx - np.append(tpx[1:], 0.0)
    return pd.DataFrame({"age": lx.index, "t": np.arange(len(lx)), "lx": lx.to_numpy(),
                         "tpx": tpx, "prob_die": q})


def life_expectancy(p: Params) -> float:
    """Model life expectancy at 67: curtate (truncated at max_age) + 0.5, as in the Excel."""
    lt = life_table(p)
    return p.retirement_age + lt["tpx"].iloc[1:].sum() + 0.5
