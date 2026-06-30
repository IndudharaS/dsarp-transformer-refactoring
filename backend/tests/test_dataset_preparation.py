"""Tests for Stage 3 dataset preparation without starting model training."""

import asyncio
from collections import Counter
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.pipeline.dataset_preparation import (
    analyze_dataset_quality,
    balance_training_rows,
    clean_training_rows,
    load_training_rows_from_mongodb,
    merge_training_datasets,
    read_training_csv,
    read_run_ids_file,
    write_training_csv,
)


def rows(label: str, count: int, prefix: str | None = None) -> list[dict[str, str]]:
    stem = prefix or label
    return [
        {"text": f"{stem} example {index}", "label": label}
        for index in range(count)
    ]


class DatasetQualityTests(unittest.TestCase):
    def test_empty_text_and_label_detection(self) -> None:
        report = analyze_dataset_quality(
            [
                {"text": "", "label": "A"},
                {"text": "valid", "label": ""},
            ]
        )
        self.assertEqual(report.empty_text, 1)
        self.assertEqual(report.empty_label, 1)

    def test_label_summary_and_imbalance_warnings(self) -> None:
        report = analyze_dataset_quality(rows("Large", 100) + rows("Small", 20))
        self.assertEqual(report.total_rows, 120)
        self.assertEqual(report.label_counts, {"Large": 100, "Small": 20})
        self.assertTrue(any("minimum is 30" in warning for warning in report.warnings))
        self.assertTrue(any("imbalance ratio" in warning for warning in report.warnings))

    def test_duplicate_and_conflicting_label_detection(self) -> None:
        report = analyze_dataset_quality(
            [
                {"text": "same text", "label": "A"},
                {"text": "same text", "label": "A"},
                {"text": "same text", "label": "B"},
            ]
        )
        self.assertEqual(report.duplicate_text_rows, 2)
        self.assertEqual(report.duplicate_text_groups, 1)
        self.assertEqual(report.conflicting_label_duplicates, 1)

    def test_cleaning_removes_invalid_and_duplicate_rows(self) -> None:
        cleaned = clean_training_rows(
            [
                {"text": "valid", "label": "A"},
                {"text": "valid", "label": "A"},
                {"text": "", "label": "A"},
                {"text": "missing label", "label": ""},
            ]
        )
        self.assertEqual(cleaned, [{"text": "valid", "label": "A"}])


class DatasetExportTests(unittest.TestCase):
    def test_run_ids_manifest_ignores_blank_values(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run_ids.json"
            path.write_text(
                '{"Tika": "run-1", "Karaf": "", "Struts": "run-2"}',
                encoding="utf-8",
            )
            self.assertEqual(read_run_ids_file(path), ["run-1", "run-2"])

    def test_training_csv_has_exact_columns(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "training.csv"
            write_training_csv(path, [{"text": "sample", "label": "Strategy", "ignored": "x"}])
            with path.open(encoding="utf-8", newline="") as input_file:
                reader = csv.DictReader(input_file)
                exported = list(reader)
            self.assertEqual(reader.fieldnames, ["text", "label"])
            self.assertEqual(exported, [{"text": "sample", "label": "Strategy"}])
            self.assertEqual(read_training_csv(path), exported)

    def test_multi_dataset_merge(self) -> None:
        merged = merge_training_datasets(
            [rows("A", 2, "run-one"), rows("B", 3, "run-two")]
        )
        self.assertEqual(len(merged), 5)
        self.assertEqual(Counter(row["label"] for row in merged), Counter({"B": 3, "A": 2}))

    def test_downsample_and_oversample(self) -> None:
        source = rows("A", 6) + rows("B", 2)
        downsampled = balance_training_rows(source, "downsample", seed=7)
        oversampled = balance_training_rows(source, "oversample", seed=7)
        self.assertEqual(Counter(row["label"] for row in downsampled), Counter({"A": 2, "B": 2}))
        self.assertEqual(Counter(row["label"] for row in oversampled), Counter({"A": 6, "B": 6}))


class FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def sort(self, *_args) -> "FakeCursor":
        return self

    async def to_list(self, length=None) -> list[dict]:
        return list(self.documents)


class FakeCollection:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def find(self, *_args, **_kwargs) -> FakeCursor:
        return FakeCursor(self.documents)

    async def count_documents(self, *_args, **_kwargs) -> int:
        return 2


class FakeDatabase:
    analysis_runs = FakeCollection([])
    training_features = FakeCollection(
        [
            {"runId": "run-1", "smellId": "S001", "text": "first", "label": "A"},
            {"runId": "run-2", "smellId": "S001", "text": "second", "label": "B"},
        ]
    )
    smells = FakeCollection([])
    classifier_predictions = FakeCollection([])


class MongoMergeTests(unittest.TestCase):
    def test_multiple_run_ids_are_merged(self) -> None:
        merged = asyncio.run(
            load_training_rows_from_mongodb(
                ["run-1", "run-2"],
                database=FakeDatabase(),
            )
        )
        self.assertEqual(len(merged), 2)
        self.assertEqual({row["label"] for row in merged}, {"A", "B"})


if __name__ == "__main__":
    unittest.main()
