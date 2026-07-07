"""Compute a smell x refactoring-label severity matrix from the mined dataset.

Reads dsarp_outputs/architecture_smell_refactoring_dataset.csv and produces,
for every (architecture_smell, refactoring_label) pair that co-occurs in the
dataset, an aggregated severity score. The score for a single row reuses the
same weighting scheme as `infer_smells()` in PYTHON_for_dataset_generation.ipynb:

    severity = max(0.0, metric_delta * smell_weight)

metric_delta = metric_before - metric_after, so severity is 0 whenever a
commit did not shrink the smell's underlying metric (improved == False).
Because only ~10% of rows in this dataset actually improved the metric, the
severity matrix alone is very sparse -- a co-occurrence frequency matrix is
also produced as a fallback/sanity-check signal.

Outputs (written next to the input CSV, in dsarp_outputs/):
    smell_refactoring_frequency_matrix.csv   -- raw co-occurrence counts
    smell_refactoring_severity_matrix.csv    -- summed severity scores
    smell_refactoring_severity_matrix_normalized.csv -- each row scaled to sum to 1
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "dsarp_outputs"
INPUT_CSV = DATA_DIR / "architecture_smell_refactoring_dataset.csv"

# Same weights as infer_smells() in PYTHON_for_dataset_generation.ipynb.
SMELL_WEIGHTS = {
    "Cyclic Dependency": 3.0,
    "Hub-like Dependency": 2.5,
    "Unstable Dependency": 2.0,
    "Large Component": 1.5,
    "Excessive Package Coupling": 1.0,
}


def load_rows(csv_path: Path = INPUT_CSV) -> pd.DataFrame:
    """Load the dataset and explode the pipe-delimited refactoring_labels column."""
    df = pd.read_csv(csv_path)
    df["severity"] = df.apply(
        lambda row: max(
            0.0,
            row["metric_delta"] * SMELL_WEIGHTS.get(row["architecture_smell"], 1.0),
        ),
        axis=1,
    )
    df["refactoring_label"] = df["refactoring_labels"].fillna("").str.split("|")
    exploded = df.explode("refactoring_label")
    exploded["refactoring_label"] = exploded["refactoring_label"].str.strip()
    exploded = exploded[exploded["refactoring_label"] != ""]
    return exploded.reset_index(drop=True)


def build_matrices(exploded: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build frequency, severity, and row-normalized severity matrices."""
    frequency = pd.crosstab(
        exploded["architecture_smell"], exploded["refactoring_label"]
    )

    severity = exploded.pivot_table(
        index="architecture_smell",
        columns="refactoring_label",
        values="severity",
        aggfunc="sum",
        fill_value=0.0,
    )
    # Include any smell/label combos that frequency has but severity doesn't
    # (all-zero severity), so both matrices share the same shape.
    severity = severity.reindex(
        index=frequency.index, columns=frequency.columns, fill_value=0.0
    )

    row_sums = severity.sum(axis=1)
    normalized = severity.div(row_sums.replace(0, pd.NA), axis=0).fillna(0.0)

    return {
        "frequency": frequency,
        "severity": severity,
        "severity_normalized": normalized,
    }


def top_labels_per_smell(normalized: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Return the top-k refactoring labels per smell by normalized severity weight."""
    rows = []
    for smell, row in normalized.iterrows():
        top = row.sort_values(ascending=False).head(k)
        for rank, (label, weight) in enumerate(top.items(), start=1):
            rows.append(
                {
                    "architecture_smell": smell,
                    "rank": rank,
                    "refactoring_label": label,
                    "severity_weight": round(float(weight), 6),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    exploded = load_rows()
    matrices = build_matrices(exploded)

    matrices["frequency"].to_csv(DATA_DIR / "smell_refactoring_frequency_matrix.csv")
    matrices["severity"].to_csv(DATA_DIR / "smell_refactoring_severity_matrix.csv")
    matrices["severity_normalized"].to_csv(
        DATA_DIR / "smell_refactoring_severity_matrix_normalized.csv"
    )

    top = top_labels_per_smell(matrices["severity_normalized"])
    top.to_csv(DATA_DIR / "smell_refactoring_top_labels.csv", index=False)

    print(f"Rows loaded: {len(exploded)} (exploded from source dataset)")
    print(f"Smells: {list(matrices['frequency'].index)}")
    print(f"Refactoring labels observed: {matrices['frequency'].shape[1]}")
    print()
    print("Top labels per smell (by normalized severity weight):")
    for smell in matrices["severity_normalized"].index:
        subset = top[top["architecture_smell"] == smell]
        nonzero = subset[subset["severity_weight"] > 0]
        if nonzero.empty:
            print(f"  {smell}: no rows improved this metric (severity all zero)")
        else:
            labels = ", ".join(
                f"{r.refactoring_label} ({r.severity_weight:.2f})"
                for r in nonzero.itertuples()
            )
            print(f"  {smell}: {labels}")
    print()
    print("Wrote matrices to:", DATA_DIR.resolve())


if __name__ == "__main__":
    main()
