"""Unit tests for the stage 2 pipeline in the DSARP backend.

These tests verify core pipeline behavior, including parsing affected element
formats, building smell objects from raw data, and ranking recommendations.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from app.pipeline.classifier_client import RuleBasedClassifier
from app.pipeline.data_loader import AnalysisData
from app.pipeline.feature_builder import (
    build_smell_objects,
    build_training_feature,
    parse_affected_elements,
)
from app.pipeline.ranker import rank_level, rank_recommendations
from app.pipeline.rule_recommender import build_rule_recommendation
from app.pipeline.validator import (
    CSVValidationError,
    validate_csv_file,
    validate_upload_type,
)


class AffectedElementsTests(unittest.TestCase):
    """Tests for parsing affected element metadata formats."""

    def test_supported_formats(self) -> None:
        """Ensure multiple supported string formats are parsed correctly."""
        self.assertEqual(parse_affected_elements("A,B,C"), ["A", "B", "C"])
        self.assertEqual(parse_affected_elements("A;B;C"), ["A", "B", "C"])
        self.assertEqual(
            parse_affected_elements('["A", "B", "C"]'),
            ["A", "B", "C"],
        )
        self.assertEqual(parse_affected_elements("[A, B, C]"), ["A", "B", "C"])
        self.assertEqual(parse_affected_elements("A"), ["A"])


class CSVValidationTests(unittest.TestCase):
    """Tests for upload type, emptiness, and required-column validation."""

    def test_rejects_non_csv_extension(self) -> None:
        with self.assertRaisesRegex(CSVValidationError, "must be a .csv"):
            validate_upload_type("smells.json", "application/json", "smells")

    def test_rejects_empty_and_header_only_files(self) -> None:
        with TemporaryDirectory() as directory:
            empty = Path(directory) / "empty.csv"
            empty.write_bytes(b"")
            with self.assertRaisesRegex(CSVValidationError, "empty"):
                validate_csv_file(empty, "smell-characteristics.csv")

            header_only = Path(directory) / "headers.csv"
            header_only.write_text(
                "smellType,Severity,Size,Strength,InstabilityGap,"
                "AffectedElements,NumberOfEdges\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CSVValidationError, "no data rows"):
                validate_csv_file(header_only, "smell-characteristics.csv")

    def test_reports_missing_columns(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "smells.csv"
            path.write_text("smellType,Severity\ncyclicDep,4.2\n", encoding="utf-8")
            missing = validate_csv_file(path, "smell-characteristics.csv")
            self.assertIn("AffectedElements", missing)
            self.assertIn("NumberOfEdges", missing)


class FeatureBuilderTests(unittest.TestCase):
    """Tests for the feature builder and smell object construction."""

    def test_builds_normalized_smell_with_matches(self) -> None:
        """Verify smell object normalization, matching dependencies, and metrics."""
        data = AnalysisData(
            smell_characteristics=pd.DataFrame(
                [
                    {
                        "system": "Tika",
                        "smellType": "cyclicDep",
                        "Severity": "4.2",
                        "Size": "3",
                        "Strength": "0.8",
                        "InstabilityGap": "",
                        "AffectedElements": "A,B",
                        "NumberOfEdges": "5",
                        "Shape": "Circle",
                        "CentralComponent": "",
                    },
                    {
                        "system": "Karaf",
                        "smellType": "godComponent",
                        "Severity": 5,
                        "Size": 1,
                        "Strength": 1,
                        "InstabilityGap": 1,
                        "AffectedElements": "Other",
                        "NumberOfEdges": 1,
                    },
                ]
            ),
            smell_affects=pd.DataFrame(
                [{"from": "A", "to": "B", "fromId": 1, "toId": 2}]
            ),
            component_metrics=pd.DataFrame(
                [
                    {
                        "name": "A",
                        "FanIn": 12,
                        "FanOut": 18,
                        "LinesOfCode": 1300,
                        "InstabilityMetric": 0.7,
                        "AbstractnessMetric": 0.1,
                        "PageRank": 0.04,
                    }
                ]
            ),
        )
        run = {"runId": "run-1", "systemName": "Tika", "version": "v1"}

        smells = build_smell_objects(run, data)

        self.assertEqual(len(smells), 1)
        self.assertEqual(smells[0]["smellId"], "S001")
        self.assertEqual(smells[0]["affectedElements"], ["A", "B"])
        self.assertEqual(smells[0]["instabilityGap"], 0.0)
        self.assertEqual(smells[0]["dependencies"], [{"from": "A", "to": "B"}])
        self.assertEqual(smells[0]["componentMetrics"][0]["fanIn"], 12.0)

        feature = build_training_feature(
            smells[0],
            "ExtractSharedComponent",
            "2026-01-01T00:00:00+00:00",
        )
        self.assertEqual(feature["label"], "ExtractSharedComponent")
        self.assertIn("Architectural smell: cyclicDep", feature["text"])
        self.assertIn("Affected components: A, B", feature["text"])


class ClassifierAndRankingTests(unittest.TestCase):
    """Tests for classifier output and recommendation ranking behavior."""

    def test_rule_classifier(self) -> None:
        """Ensure the fallback rule-based classifier returns expected predictions."""
        prediction = RuleBasedClassifier().predict("unstableDep")
        self.assertEqual(prediction.strategy, "DependencyInversion")
        self.assertEqual(prediction.confidence, 0.80)

    def test_equal_values_normalize_to_half(self) -> None:
        """Verify equal metric values normalize to 0.5 and preserve ranking order."""
        recommendations = [
            {
                "severity": 1,
                "size": 1,
                "strength": 1,
                "instabilityGap": 1,
                "numberOfEdges": 1,
                "recommendationConfidence": 0.75,
                "classifierConfidence": 0.80,
            },
            {
                "severity": 1,
                "size": 1,
                "strength": 1,
                "instabilityGap": 1,
                "numberOfEdges": 1,
                "recommendationConfidence": 0.75,
                "classifierConfidence": 0.80,
            },
        ]

        ranked = rank_recommendations(recommendations)

        self.assertEqual(ranked[0]["smellPriorityScore"], 0.5)
        self.assertEqual(ranked[0]["rankPosition"], 1)
        self.assertEqual(ranked[1]["rankPosition"], 2)

    def test_rank_boundaries(self) -> None:
        """Check that score boundaries produce the expected rank levels."""
        self.assertEqual(rank_level(0.80), "Critical")
        self.assertEqual(rank_level(0.60), "High")
        self.assertEqual(rank_level(0.40), "Medium")
        self.assertEqual(rank_level(0.39), "Low")

    def test_rule_recommendations_are_structured(self) -> None:
        for smell_type in ("godComponent", "unstableDep", "cyclicDep"):
            result = build_rule_recommendation(
                {"smellType": smell_type, "affectedElements": ["A"]}
            )
            self.assertTrue(result["recommendation"])
            self.assertTrue(result["reason"])
            self.assertTrue(result["steps"])
            self.assertIn(result["risk"], {"Medium", "High"})

    def test_ranking_sorts_descending(self) -> None:
        base = {
            "size": 1,
            "strength": 1,
            "instabilityGap": 1,
            "numberOfEdges": 1,
            "recommendationConfidence": 0.75,
            "classifierConfidence": 0.80,
        }
        ranked = rank_recommendations(
            [{**base, "severity": 1}, {**base, "severity": 10}]
        )
        self.assertGreaterEqual(
            ranked[0]["finalRankingScore"],
            ranked[1]["finalRankingScore"],
        )


if __name__ == "__main__":
    unittest.main()
