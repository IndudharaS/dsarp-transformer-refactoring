"""Helpers for resolving uploaded file paths and loading analysis CSV data.

This module defines the expected analysis data structure, maps upload keys to
filename conventions, and provides utilities to validate and read CSV files
submitted as part of a run.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from app.config import get_settings


# Load application settings once and reuse them for path resolution.
settings = get_settings()


@dataclass(frozen=True)
class AnalysisData:
    """Holds the analysis data tables loaded from uploaded CSV files."""

    smell_characteristics: pd.DataFrame
    smell_affects: pd.DataFrame
    component_metrics: pd.DataFrame


# Mapping from expected upload keys to the stored CSV filenames.
FILE_KEYS = {
    "smellCharacteristics": "smell-characteristics.csv",
    "smellAffects": "smell-affects.csv",
    "componentMetrics": "component-metrics.csv",
}


def resolve_stored_path(stored_path: str) -> Path:
    """Resolve a stored file path to an absolute Path object.

    If the provided path is already absolute, it is returned unchanged. Otherwise,
    the path is resolved relative to the configured base path.
    """
    path = Path(stored_path)
    if path.is_absolute():
        return path
    return settings.base_path / path


def load_analysis_data(uploaded_files: Mapping[str, Any]) -> AnalysisData:
    """Load and validate analysis CSV files from uploaded file metadata.

    The uploaded_files mapping is expected to contain a `files` entry with
    metadata for each required dataset. Each dataset is validated, resolved to a
    file path, and loaded into a pandas DataFrame.
    """
    file_metadata = uploaded_files.get("files")
    if not isinstance(file_metadata, Mapping):
        raise ValueError("Uploaded file metadata is missing the files object.")

    paths: dict[str, Path] = {}
    for key in FILE_KEYS:
        metadata = file_metadata.get(key)
        if not isinstance(metadata, Mapping) or not metadata.get("storedPath"):
            raise ValueError(f"Uploaded file metadata is missing {key}.")

        # Resolve the stored path and verify that the file exists.
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
    except pd.errors.EmptyDataError as error:
        raise ValueError("One or more uploaded CSV files are empty.") from error
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        # Wrap CSV parsing errors in a ValueError with a descriptive message.
        raise ValueError(f"Unable to parse uploaded CSV files: {error}") from error
