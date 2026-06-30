"""Utilities for preparing Stage 2 outputs for transformer training."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import random
from typing import Any, Iterable, Mapping, Sequence

from app.db.mongo import get_database
from app.pipeline.feature_builder import build_training_feature


TrainingRow = dict[str, str]


@dataclass(frozen=True)
class DatasetQualityReport:
    total_rows: int
    label_counts: dict[str, int]
    empty_text: int
    empty_label: int
    duplicate_text_rows: int
    duplicate_text_groups: int
    conflicting_label_duplicates: int
    largest_to_smallest_ratio: float | None
    warnings: list[str]
    ready: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_rows(rows: Iterable[Mapping[str, Any]]) -> list[TrainingRow]:
    """Keep exactly text and label while normalizing values to strings."""
    return [
        {
            "text": "" if row.get("text") is None else str(row.get("text")).strip(),
            "label": "" if row.get("label") is None else str(row.get("label")).strip(),
        }
        for row in rows
    ]


def analyze_dataset_quality(rows: Sequence[Mapping[str, Any]]) -> DatasetQualityReport:
    """Measure missing values, duplicates, label counts, and imbalance."""
    normalized = normalize_rows(rows)
    empty_text = sum(not row["text"] for row in normalized)
    empty_label = sum(not row["label"] for row in normalized)
    label_counts = dict(
        sorted(Counter(row["label"] for row in normalized if row["label"]).items())
    )

    labels_by_text: dict[str, list[str]] = defaultdict(list)
    for row in normalized:
        if row["text"]:
            labels_by_text[row["text"]].append(row["label"])
    duplicate_groups = {
        text: labels for text, labels in labels_by_text.items() if len(labels) > 1
    }
    duplicate_rows = sum(len(labels) - 1 for labels in duplicate_groups.values())
    conflicting = sum(
        len(set(labels)) > 1 for labels in duplicate_groups.values()
    )

    counts = list(label_counts.values())
    ratio = None
    if counts:
        ratio = round(max(counts) / min(counts), 6)

    warnings: list[str] = []
    if empty_text:
        warnings.append(f"{empty_text} rows have empty text.")
    if empty_label:
        warnings.append(f"{empty_label} rows have empty labels.")
    if duplicate_rows:
        warnings.append(f"{duplicate_rows} duplicate text rows were detected.")
    if conflicting:
        warnings.append(
            f"{conflicting} duplicate text groups contain conflicting labels."
        )
    if len(label_counts) < 2:
        warnings.append("The dataset contains fewer than two labels.")
    for label, count in label_counts.items():
        if count < 30:
            warnings.append(f"Label '{label}' has only {count} examples; minimum is 30.")
    if ratio is not None and ratio > 3:
        warnings.append(
            f"Class imbalance ratio is {ratio:.2f}:1; maximum recommended ratio is 3:1."
        )

    return DatasetQualityReport(
        total_rows=len(normalized),
        label_counts=label_counts,
        empty_text=empty_text,
        empty_label=empty_label,
        duplicate_text_rows=duplicate_rows,
        duplicate_text_groups=len(duplicate_groups),
        conflicting_label_duplicates=conflicting,
        largest_to_smallest_ratio=ratio,
        warnings=warnings,
        ready=not warnings,
    )


def clean_training_rows(rows: Sequence[Mapping[str, Any]]) -> list[TrainingRow]:
    """Remove empty records and duplicate text, preserving first occurrence."""
    cleaned: list[TrainingRow] = []
    seen_text: set[str] = set()
    for row in normalize_rows(rows):
        if not row["text"] or not row["label"] or row["text"] in seen_text:
            continue
        cleaned.append(row)
        seen_text.add(row["text"])
    return cleaned


def balance_training_rows(
    rows: Sequence[Mapping[str, Any]],
    mode: str,
    *,
    target_count: int | None = None,
    seed: int = 42,
) -> list[TrainingRow]:
    """Balance classes using deterministic downsampling or oversampling."""
    normalized = normalize_rows(rows)
    groups: dict[str, list[TrainingRow]] = defaultdict(list)
    for row in normalized:
        if row["text"] and row["label"]:
            groups[row["label"]].append(row)
    if not groups:
        return []
    if mode not in {"downsample", "oversample"}:
        raise ValueError("mode must be 'downsample' or 'oversample'.")
    if target_count is not None and target_count < 1:
        raise ValueError("target_count must be at least 1.")

    randomizer = random.Random(seed)
    class_counts = [len(group) for group in groups.values()]
    target = target_count or (
        min(class_counts) if mode == "downsample" else max(class_counts)
    )
    balanced: list[TrainingRow] = []
    for label in sorted(groups):
        group = list(groups[label])
        randomizer.shuffle(group)
        if mode == "downsample":
            balanced.extend(group[: min(target, len(group))])
        else:
            if len(group) < target:
                balanced.extend(group)
                balanced.extend(randomizer.choices(group, k=target - len(group)))
            else:
                balanced.extend(group[:target])
    randomizer.shuffle(balanced)
    return balanced


def read_training_csv(path: Path) -> list[TrainingRow]:
    """Read text and label columns from an existing Stage 2 export."""
    with path.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames is None or not {"text", "label"}.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain text and label columns.")
        return normalize_rows(reader)


def read_run_ids_file(path: Path) -> list[str]:
    """Read non-empty runIds from a project-name-to-runId JSON manifest."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON.") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object of project names to runIds.")

    run_ids: list[str] = []
    for project, run_id in payload.items():
        if not isinstance(project, str) or not isinstance(run_id, str):
            raise ValueError("Every runIds manifest key and value must be a string.")
        cleaned = run_id.strip()
        if cleaned and cleaned not in run_ids:
            run_ids.append(cleaned)
    return run_ids


def merge_training_datasets(datasets: Iterable[Iterable[Mapping[str, Any]]]) -> list[TrainingRow]:
    """Merge any number of run or CSV datasets into one normalized dataset."""
    return [row for dataset in datasets for row in normalize_rows(dataset)]


def write_training_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write a CSV containing exactly text and label columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(normalize_rows(rows))


async def load_training_rows_from_mongodb(
    run_ids: Sequence[str],
    database: Any | None = None,
) -> list[TrainingRow]:
    """Load multiple runs, falling back to Stage 2 smells and predictions."""
    if not run_ids:
        return []
    db = database or get_database()
    existing_runs = await db.analysis_runs.count_documents(
        {"runId": {"$in": list(run_ids)}}
    )
    if existing_runs != len(set(run_ids)):
        raise ValueError("One or more requested runIds do not exist.")

    features = await (
        db.training_features.find(
            {"runId": {"$in": list(run_ids)}},
            {"_id": 0, "runId": 1, "text": 1, "label": 1},
        )
        .sort([("runId", 1), ("smellId", 1)])
        .to_list(length=None)
    )
    runs_with_features = {feature["runId"] for feature in features}

    for run_id in run_ids:
        if run_id in runs_with_features:
            continue
        smells = await (
            db.smells.find({"runId": run_id}, {"_id": 0})
            .sort("smellId", 1)
            .to_list(length=None)
        )
        predictions = await db.classifier_predictions.find(
            {"runId": run_id},
            {"_id": 0},
        ).to_list(length=None)
        prediction_by_smell = {
            prediction["smellId"]: prediction for prediction in predictions
        }
        for smell in smells:
            prediction = prediction_by_smell.get(smell["smellId"])
            if prediction:
                feature = build_training_feature(
                    smell,
                    prediction["predictedStrategy"],
                    prediction.get("createdAt", smell.get("createdAt", "")),
                )
                features.append(feature)

    return normalize_rows(features)
