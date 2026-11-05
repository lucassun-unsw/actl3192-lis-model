"""Age Pension means test: deeming, assets test, income test.

All functions work on numpy arrays or scalars, annual amounts in today's dollars.
"""

import numpy as np

from .params import Params


def deemed_income(financial_assets, p: Params):
    """Two tier deemed income on financial assets."""
    a = np.asarray(financial_assets, dtype=float)
    return (np.minimum(a, p.deeming_threshold) * p.deeming_lower
            + np.maximum(a - p.deeming_threshold, 0.0) * p.deeming_upper)


def assets_test_pension(assessed_assets, p: Params):
    """Pension payable under the assets test."""
    a = np.asarray(assessed_assets, dtype=float)
    return np.maximum(0.0, p.max_rate - np.maximum(0.0, a - p.assets_free_area) * p.assets_taper)


def income_test_pension(assessed_income, p: Params):
    """Pension payable under the income test."""
    i = np.asarray(assessed_income, dtype=float)
    return np.maximum(0.0, p.max_rate - np.maximum(0.0, i - p.income_free_area) * p.income_taper)


def age_pension(assessed_assets, assessed_income, p: Params):
    """Age Pension = lower of the two tests, plus which test binds.

    Binding test follows the Excel: "nil" if no pension, "assets" if the assets
    test pension is lower or equal, otherwise "income".
    """
    at = assets_test_pension(assessed_assets, p)
    it = income_test_pension(assessed_income, p)
    ap = np.minimum(at, it)
    binding = np.where(ap == 0, "nil", np.where(at <= it, "assets", "income"))
    return ap, at, it, binding
