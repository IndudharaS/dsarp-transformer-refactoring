"""Simple classifier client definitions for smell-to-strategy prediction.

This module defines the prediction model contract, a rule-based classifier
implementation, and a helper that returns the default classifier instance.
"""

from dataclasses import dataclass
from typing import Protocol


# Supported strategy labels that the classifier may return.
POSSIBLE_STRATEGIES = (
    "ExtractComponent",
    "SplitResponsibilities",
    "DependencyInversion",
    "IntroduceInterface",
    "ExtractSharedComponent",
    "FacadePattern",
    "MediatorPattern",
    "LayerReorganization",
)


@dataclass(frozen=True)
class ClassifierPrediction:
    """Represents a single classifier output prediction."""

    strategy: str
    confidence: float
    model: str


class ClassifierClient(Protocol):
    """Protocol defining the classifier interface used by the pipeline."""

    def predict(self, smell_type: str) -> ClassifierPrediction:
        """Predict a remediation strategy for the given smell type."""
        ...


class RuleBasedClassifier:
    """A simple rule-based classifier implementation.

    This classifier maps known smell types to a fixed strategy and returns a
    fixed confidence score. It provides a baseline for classifier behavior.
    """

    model_name = "rule-classifier-baseline"

    # Static mapping of smell types to suggested remediation strategies.
    rules = {
        "godComponent": "ExtractComponent",
        "unstableDep": "DependencyInversion",
        "cyclicDep": "ExtractSharedComponent",
    }

    def predict(self, smell_type: str) -> ClassifierPrediction:
        """Return a strategy prediction for a smell type using rule lookup."""
        # Lookup the rule for the smell type and raise if none exists.
        strategy = self.rules.get(smell_type)
        if strategy is None:
            raise ValueError(f"No classifier rule exists for {smell_type}.")

        # Build and return the structured prediction result.
        return ClassifierPrediction(
            strategy=strategy,
            confidence=0.80,
            model=self.model_name,
        )


def get_classifier() -> ClassifierClient:
    """Return the default classifier used by the pipeline."""
    return RuleBasedClassifier()
