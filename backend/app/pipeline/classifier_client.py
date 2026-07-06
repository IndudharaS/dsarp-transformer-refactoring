"""Classifier adapters with a local transformer and deterministic fallback."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.config import get_settings

POSSIBLE_STRATEGIES = (
    "ExtractComponent", "SplitResponsibilities", "DependencyInversion",
    "IntroduceInterface", "ExtractSharedComponent", "FacadePattern",
    "MediatorPattern", "LayerReorganization",
)


@dataclass(frozen=True)
class ClassifierPrediction:
    strategy: str
    confidence: float
    model: str


class ClassifierClient(Protocol):
    def predict(self, smell_type: str, text: str | None = None) -> ClassifierPrediction: ...


class RuleBasedClassifier:
    model_name = "rule-classifier-baseline"
    rules = {
        "godComponent": "ExtractComponent",
        "unstableDep": "DependencyInversion",
        "cyclicDep": "ExtractSharedComponent",
    }

    def predict(self, smell_type: str, text: str | None = None) -> ClassifierPrediction:
        del text
        strategy = self.rules.get(smell_type)
        if strategy is None:
            raise ValueError(f"No classifier rule exists for {smell_type}.")
        return ClassifierPrediction(strategy, 0.80, self.model_name)


class TransformerClassifier:
    """Lazy local Hugging Face classifier exported by the Colab notebook."""

    model_name = "codebert-refactoring-classifier"

    def __init__(self, model_dir: Path, local_files_only: bool = True) -> None:
        import joblib
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=local_files_only)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            model_dir, local_files_only=local_files_only
        ).to(self._device)
        self._model.eval()
        self._encoder: Any = joblib.load(model_dir / "label_encoder.pkl")

    def predict(self, smell_type: str, text: str | None = None) -> ClassifierPrediction:
        encoded = self._tokenizer(
            text or f"Architectural smell: {smell_type}.",
            return_tensors="pt", truncation=True, max_length=256,
        )
        encoded = {key: value.to(self._device) for key, value in encoded.items()}
        with self._torch.no_grad():
            probabilities = self._torch.softmax(self._model(**encoded).logits, dim=-1)[0]
        label_id = int(self._torch.argmax(probabilities).item())
        strategy = str(self._encoder.inverse_transform([label_id])[0])
        if strategy not in POSSIBLE_STRATEGIES:
            raise ValueError(f"Transformer returned unsupported strategy {strategy}.")
        return ClassifierPrediction(
            strategy, round(float(probabilities[label_id].item()), 6), self.model_name
        )


def get_classifier() -> ClassifierClient:
    """Use the local transformer when installed; otherwise use Stage 2 rules."""
    settings = get_settings()
    model_dir = settings.transformer_model_path
    if (model_dir / "config.json").exists() and (model_dir / "label_encoder.pkl").exists():
        try:
            return TransformerClassifier(model_dir, settings.transformer_local_files_only)
        except (ImportError, OSError, ValueError):
            pass
    return RuleBasedClassifier()
