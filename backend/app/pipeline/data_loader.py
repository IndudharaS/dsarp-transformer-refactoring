from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from app.config import get_settings


settings = get_settings()


@dataclass(frozen=True)
class AnalysisData:
    smell_characteristics: pd.DataFrame
    smell_affects: pd.DataFrame
    component_metrics: pd.DataFrame


FILE_KEYS = {
    "smellCharacteristics": "smell-characteristics.csv",
    "smellAffects": "smell-affects.csv",
    "componentMetrics": "component-metrics.csv",
}


def resolve_stored_path(stored_path: str) -> Path:
    path = Path(stored_path)
    if path.is_absolute():
        return path
    return settings.base_path / path


def load_analysis_data(uploaded_files: Mapping[str, Any]) -> AnalysisData:
    file_metadata = uploaded_files.get("files")
    if not isinstance(file_metadata, Mapping):
        raise ValueError("Uploaded file metadata is missing the files object.")

    paths: dict[str, Path] = {}
    for key in FILE_KEYS:
        metadata = file_metadata.get(key)
        if not isinstance(metadata, Mapping) or not metadata.get("storedPath"):
            raise ValueError(f"Uploaded file metadata is missing {key}.")

        path = resolve_stored_path(str(metadata["storedPath"]))
        if not path.is_file():
            raise FileNotFoundError(f"Uploaded file was not found: {path}")
        paths[key] = path

    try:
        return AnalysisData(
            smell_characteristics=pd.read_csv(
                paths["smellCharacteristics"],
                keep_default_na=True,
            ),
            smell_affects=pd.read_csv(
                paths["smellAffects"],
                keep_default_na=True,
            ),
            component_metrics=pd.read_csv(
                paths["componentMetrics"],
                keep_default_na=True,
            ),
        )
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        raise ValueError(f"Unable to parse uploaded CSV files: {error}") from error
