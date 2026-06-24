"""Unit tests for the stage 2 pipeline in the DSARP backend.

These tests verify core pipeline behavior, including parsing affected element
formats, building smell objects from raw data, and ranking recommendations.
"""

import unittest

import pandas as pd

from app.pipeline.classifier_client import RuleBasedClassifier
from app.pipeline.data_loader import AnalysisData
from app.pipeline.feature_builder import (
    build_smell_objects,
    parse_affected_elements,
)
from app.pipeline.ranker import rank_level, rank_recommendations


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


if __name__ == "__main__":
    unittest.main()
