"""Combine DSARP exports and the mined Apache dataset for Colab training.

The mined data is weakly labelled: its architecture smell is mapped to one of
DSARP's strategy classes. Provenance is retained in the generated report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


FRIEND_SMELL_LABELS = {
    "Cyclic Dependency": "ExtractSharedComponent",
    "Large Component": "ExtractComponent",
    "Hub-like Dependency": "MediatorPattern",
    "Excessive Package Coupling": "LayerReorganization",
    "Unstable Dependency": "DependencyInversion",
}


def load_dsarp_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str).fillna("")
    if list(frame.columns) != ["text", "label"]:
        raise ValueError(f"{path} must contain exactly the columns text,label")
    return frame.assign(source=f"dsarp:{path.name}")


def load_mined_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path).fillna("")
    required = {"architecture_smell", "input_text", "repository", "commit"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
    frame["label"] = frame["architecture_smell"].map(FRIEND_SMELL_LABELS)
    frame = frame[frame["label"].notna()].copy()
    frame["text"] = frame.apply(
        lambda row: (
            f"Repository: {row['repository']}. {row['input_text']} "
            f"Observed refactoring commit: {row['commit']}."
        ),
        axis=1,
    )
    frame["source"] = "apache-mined-weak-label"
    return frame[["text", "label", "source"]]


def prepare_dataset(
    dsarp_paths: list[Path], mined_path: Path | None
) -> tuple[pd.DataFrame, dict[str, object]]:
    frames = [load_dsarp_csv(path) for path in dsarp_paths]
    if mined_path:
        frames.append(load_mined_csv(mined_path))
    if not frames:
        raise ValueError("Provide at least one --dsarp-csv or --mined-csv input.")

    combined = pd.concat(frames, ignore_index=True)
    combined["text"] = combined["text"].astype(str).str.strip()
    combined["label"] = combined["label"].astype(str).str.strip()
    empty_rows = int(((combined["text"] == "") | (combined["label"] == "")).sum())
    duplicate_rows = int(combined.duplicated(["text", "label"]).sum())
    combined = combined[(combined["text"] != "") & (combined["label"] != "")]
    combined = combined.drop_duplicates(["text", "label"]).reset_index(drop=True)

    counts = combined["label"].value_counts().to_dict()
    report: dict[str, object] = {
        "rows": len(combined),
        "labelCounts": {str(key): int(value) for key, value in counts.items()},
        "sourceCounts": {
            str(key): int(value) for key, value in combined["source"].value_counts().items()
        },
        "removedEmptyRows": empty_rows,
        "removedDuplicateRows": duplicate_rows,
        "weakLabelMapping": FRIEND_SMELL_LABELS,
        "warnings": [],
    }
    warnings = report["warnings"]
    assert isinstance(warnings, list)
    for label, count in counts.items():
        if count < 30:
            warnings.append(f"{label} has only {count} examples (minimum recommended: 30).")
    if counts and max(counts.values()) > 3 * min(counts.values()):
        warnings.append("Largest class is more than 3x the smallest class.")
    return combined[["text", "label"]], report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsarp-csv", action="append", default=[], type=Path)
    parser.add_argument("--mined-csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reports/stage3-codebert.csv"))
    args = parser.parse_args()
    dataset, report = prepare_dataset(args.dsarp_csv, args.mined_csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(args.output, index=False)
    report_path = args.output.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {args.output} and {report_path}")


if __name__ == "__main__":
    main()
