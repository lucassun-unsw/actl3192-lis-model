"""Reconciliation against the Excel model (ACTL3192_early_model.xlsx), base parameters.

Every value must match within $5.
"""

import openpyxl
import pytest

from lis_model.metrics import compare, age_of_death
from lis_model.mortality import life_expectancy
from lis_model.params import BASE, ROOT
from lis_model.projection import project
from lis_model.scenarios import ALL_ABP, CURRENT_LIS

TOL = 5.0

TARGETS = {
    # balance: (AP67 all ABP, AP67 LIS, dPV AP, dPV income, dPV bequest, death at 75 d bequest)
    400_000: (26_954, 28_723, -10_303, 42_509, -65_905, -168_080),
    500_000: (19_154, 26_954, 24_874, 90_889, -82_382, -210_100),
    650_000: (7_454, 17_594, 83_758, 169_578, -107_096, -273_130),
}


@pytest.fixture(scope="module", params=sorted(TARGETS))
def case(request):
    bal = request.param
    base, lis = project(bal, ALL_ABP, BASE), project(bal, CURRENT_LIS, BASE)
    return bal, compare(lis, base, BASE), age_of_death(lis, base, 75)


def test_age_pension_67_all_abp(case):
    bal, c, _ = case
    assert c["age_pension_67_all_abp"] == pytest.approx(TARGETS[bal][0], abs=TOL)


def test_age_pension_67_lis(case):
    bal, c, _ = case
    assert c["age_pension_67"] == pytest.approx(TARGETS[bal][1], abs=TOL)


def test_change_pv_age_pension(case):
    bal, c, _ = case
    assert c["d_pv_age_pension"] == pytest.approx(TARGETS[bal][2], abs=TOL)


def test_change_pv_income(case):
    bal, c, _ = case
    assert c["d_pv_income"] == pytest.approx(TARGETS[bal][3], abs=TOL)


def test_change_pv_bequest(case):
    bal, c, _ = case
    assert c["d_pv_bequest"] == pytest.approx(TARGETS[bal][4], abs=TOL)


def test_death_at_75_change_in_bequest(case):
    bal, _, d = case
    assert d["d_bequest"] == pytest.approx(TARGETS[bal][5], abs=TOL)


def test_life_expectancy():
    assert life_expectancy(BASE) == pytest.approx(87.9, abs=0.05)


# Every projection cell of the Excel Member_* sheets (rows 6 to 39), not just the headline targets
EXCEL = ROOT / "Data" / "ACTL3192_early_model.xlsx"
CELL_COLS = {"F": ("abp", "abp_open"), "G": ("abp", "drawdown"), "H": ("abp", "deemed_income"),
             "I": ("abp", "ap_assets_test"), "J": ("abp", "ap_income_test"), "K": ("abp", "age_pension"),
             "L": ("abp", "total_income"), "M": ("abp", "abp_close"), "N": ("abp", "binding_test"),
             "O": ("lis", "abp_open"), "P": ("lis", "drawdown"), "Q": ("lis", "lis_payment"),
             "R": ("lis", "lis_assessed_assets"), "S": ("lis", "assessed_income"), "T": ("lis", "ap_assets_test"),
             "U": ("lis", "ap_income_test"), "V": ("lis", "age_pension"), "W": ("lis", "total_income"),
             "X": ("lis", "abp_close"), "Y": ("lis", "binding_test")}


@pytest.fixture(scope="module")
def excel():
    return openpyxl.load_workbook(EXCEL, data_only=True, read_only=True)


@pytest.mark.parametrize("bal", sorted(TARGETS))
def test_every_excel_cell(excel, bal):
    ws = excel[f"Member_{bal // 1000}k"]
    rows = {c: [r[0].value for r in ws[f"{c}6:{c}39"]] for c in CELL_COLS}
    proj = {"abp": project(bal, ALL_ABP, BASE), "lis": project(bal, CURRENT_LIS, BASE)}
    for col, (case, field) in CELL_COLS.items():
        ours = list(proj[case][field])
        if isinstance(rows[col][0], str):
            assert ours == rows[col], f"{col} {field}"
        else:
            assert ours == pytest.approx(rows[col], abs=1e-6), f"{col} {field}"
