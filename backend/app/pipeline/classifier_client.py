from dataclasses import dataclass
from typing import Protocol


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
    strategy: str
    confidence: float
    model: str


class ClassifierClient(Protocol):
    def predict(self, smell_type: str) -> ClassifierPrediction:
        ...


class RuleBasedClassifier:
    model_name = "rule-classifier-baseline"
    rules = {
        "godComponent": "ExtractComponent",
        "unstableDep": "DependencyInversion",
        "cyclicDep": "ExtractSharedComponent",
    }

    def predict(self, smell_type: str) -> ClassifierPrediction:
        strategy = self.rules.get(smell_type)
        if strategy is None:
            raise ValueError(f"No classifier rule exists for {smell_type}.")
        return ClassifierPrediction(
            strategy=strategy,
            confidence=0.80,
            model=self.model_name,
        )


def get_classifier() -> ClassifierClient:
    return RuleBasedClassifier()
