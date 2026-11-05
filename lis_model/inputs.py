"""Group supplied inputs: population weights and cohort counts.

Each file is created with clearly labelled PLACEHOLDER values if it does not exist.
A file counts as a placeholder while its first line or its `source` column says
PLACEHOLDER; the group replaces the numbers and the label with ATO/ABS data.
"""

import pandas as pd

from .params import ROOT, Params

COUNTS_NOTE = ("# PLACEHOLDER counts (not data): {n} new retirees per balance member per entry year. "
               "Replace with ATO/ABS numbers. Columns: year (entry year 1..{years}), balance_member, count.")
COHORT_INPUTS_NOTE = ("# PLACEHOLDER values (not data), chosen only so the derived counts equal {n} per balance member "
                      "per year. count = women_turning_67 x share_in_band x single_share x homeowner_share. "
                      "Replace with ABS/ATO numbers and set the source column.")
WEIGHTS_SOURCE = "PLACEHOLDER: equal weights until ATO numbers are supplied"
COHORT_INPUT_COLS = ["women_turning_67", "share_in_band", "single_share", "homeowner_share"]
# Source column for each derived counts input (a single "source" column is also accepted)
COHORT_SOURCE_COLS = {"women_turning_67": "women_source", "share_in_band": "band_source",
                      "single_share": "single_source", "homeowner_share": "homeowner_source"}


def _is_placeholder(path, df):
    """True if the first line or any entry of a *source column is labelled PLACEHOLDER."""
    with open(path) as f:
        first = f.readline()
    in_source = any(df[c].astype(str).str.contains("PLACEHOLDER").any() for c in df.columns if "source" in c)
    return "PLACEHOLDER" in first or bool(in_source)


def _check_members(df, p: Params, what):
    missing = sorted(set(p.balances) - set(df["balance_member"]))
    if missing:
        raise ValueError(f"{what} has no row for balance members {missing}")


# --- Weights ---

def write_placeholder_weights(p: Params, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"balance_member": list(p.balances), "weight": 1.0,
                  "source": WEIGHTS_SOURCE}).to_csv(path, index=False)


def load_weights(p: Params) -> tuple[pd.DataFrame, bool]:
    """Weights table (balance_member, weight, source) and whether it is still a placeholder."""
    if p.weights is not None:
        df = pd.DataFrame(list(p.weights), columns=["balance_member", "weight"]).assign(source="set in params")
        return df, False
    path = ROOT / p.weights_file
    if not path.exists():
        write_placeholder_weights(p, path)
    df = pd.read_csv(path, comment="#")
    _check_members(df, p, p.weights_file)
    return df, _is_placeholder(path, df)


def weight_map(p: Params) -> dict:
    """balance -> weight, from p.weights if set, otherwise from the weights file."""
    df, _ = load_weights(p)
    return dict(zip(df["balance_member"], df["weight"].astype(float)))


def with_weights(p: Params) -> Params:
    """Copy of p with the weights file read into p.weights, so it is read only once."""
    return p if p.weights is not None else p.with_(weights=tuple(weight_map(p).items()))


# --- Cohort counts ---

def write_placeholder_counts(p: Params, path):
    """Direct counts file with a clear note on the first line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"year": t, "balance_member": b, "count": p.placeholder_count}
            for t in range(1, p.scale_up_years + 1) for b in p.balances]
    with open(path, "w") as f:
        f.write(COUNTS_NOTE.format(n=p.placeholder_count, years=p.scale_up_years) + "\n")
        pd.DataFrame(rows).to_csv(f, index=False)


def write_placeholder_cohort_inputs(p: Params, path):
    """Derived counts inputs file, one row per entry year and balance member."""
    path.parent.mkdir(parents=True, exist_ok=True)
    women, band, single, home = p.placeholder_cohort_inputs
    rows = [{"year": t, "balance_member": b, "women_turning_67": women, "share_in_band": band,
             "single_share": single, "homeowner_share": home, "source": "PLACEHOLDER"}
            for t in range(1, p.scale_up_years + 1) for b in p.balances]
    with open(path, "w") as f:
        f.write(COHORT_INPUTS_NOTE.format(n=p.placeholder_count) + "\n")
        pd.DataFrame(rows).to_csv(f, index=False)


def derived_counts(inputs: pd.DataFrame) -> pd.DataFrame:
    """count = women turning 67 x share in band x single share x homeowner share."""
    count = inputs[COHORT_INPUT_COLS].prod(axis=1)
    return inputs[["year", "balance_member"]].assign(count=count)


def load_cohort_inputs(p: Params) -> tuple[pd.DataFrame, bool]:
    """Derived counts inputs file and whether any of it is still a placeholder."""
    path = ROOT / p.cohort_inputs_file
    if not path.exists():
        write_placeholder_cohort_inputs(p, path)
    df = pd.read_csv(path, comment="#")
    return df, _is_placeholder(path, df)


def load_cohort_counts(p: Params, homeowner_share=None) -> tuple[pd.DataFrame, bool]:
    """Cohort counts (year, balance_member, count) from the source chosen in params, and
    whether they are still placeholders.

    `homeowner_share` overrides the file value (derived counts only; used for the sensitivity).
    """
    if homeowner_share is not None:
        if p.count_source != "derived":
            raise ValueError("homeowner_share can only be changed for count_source = 'derived'")
        df, placeholder = load_cohort_inputs(p)
        counts = derived_counts(df.assign(homeowner_share=homeowner_share))
        _check_members(counts, p, p.cohort_inputs_file)
        return counts, placeholder
    if p.count_source == "direct":
        path, writer = ROOT / p.cohort_counts_file, write_placeholder_counts
    elif p.count_source == "derived":
        path, writer = ROOT / p.cohort_inputs_file, write_placeholder_cohort_inputs
    else:
        raise ValueError(f"Unknown count_source '{p.count_source}'")
    if not path.exists():
        writer(p, path)
    df = pd.read_csv(path, comment="#")
    placeholder = _is_placeholder(path, df)
    counts = derived_counts(df) if p.count_source == "derived" else df[["year", "balance_member", "count"]]
    _check_members(counts, p, path.name)
    return counts, placeholder


def ensure_input_files(p: Params):
    """Create any missing input file with placeholders, so the group can see every option."""
    for name, writer in [(p.weights_file, write_placeholder_weights), (p.cohort_counts_file, write_placeholder_counts),
                         (p.cohort_inputs_file, write_placeholder_cohort_inputs)]:
        if not (ROOT / name).exists():
            writer(p, ROOT / name)


def homeowner_share_in_file(p: Params) -> float:
    """The single homeowner share used in the derived counts file."""
    values = load_cohort_inputs(p)[0]["homeowner_share"].unique()
    if len(values) != 1:
        raise ValueError(f"Expected one homeowner_share in {p.cohort_inputs_file}, found {sorted(values)}")
    return float(values[0])


def input_rows(p: Params) -> pd.DataFrame:
    """One row per distinct input value in the weights and cohort inputs files, with its source,
    for the parameters sheet."""
    rows = []
    w, w_ph = load_weights(p.with_(weights=None))  # always the file, even after with_weights()
    for _, r in w.iterrows():
        rows.append({"parameter": f"weights.csv: weight {r['balance_member']:,.0f}", "value": str(r["weight"]),
                     "description": "Population weight (share of women 65 to 69 with super in the band)",
                     "source": r["source"], "label": "placeholder" if w_ph else "evidence"})
    df, _ = load_cohort_inputs(p)
    for col in COHORT_INPUT_COLS:
        src_col = COHORT_SOURCE_COLS[col] if COHORT_SOURCE_COLS[col] in df else "source"
        for (value, src), g in df.groupby([col, src_col], sort=False):
            members = sorted(g["balance_member"].unique())
            where = "all members" if len(members) == len(p.balances) else ", ".join(f"{m:,.0f}" for m in members)
            rows.append({"parameter": f"cohort_inputs.csv: {col} ({where})", "value": str(value),
                         "description": f"Derived counts input, used when count_source = 'derived' "
                                        f"(now '{p.count_source}')",
                         "source": src, "label": "placeholder" if "PLACEHOLDER" in str(src) else "evidence"})
    return pd.DataFrame(rows)
