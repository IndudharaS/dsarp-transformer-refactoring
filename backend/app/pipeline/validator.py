"""Validators for uploaded analysis CSV datasets.

This module defines the expected CSV schema for each uploaded analysis file and
provides helper functions that check for missing required columns in both file
paths and loaded pandas DataFrames.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Set

import pandas as pd

from app.pipeline.data_loader import AnalysisData


# Required column names for each expected CSV file.
REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "smell-characteristics.csv": [
        "smellType",
        "Severity",
        "Size",
        "Strength",
        "InstabilityGap",
        "AffectedElements",
        "NumberOfEdges",
    ],
    "smell-affects.csv": [
        "from",
        "to",
        "fromId",
        "toId",
    ],
    "component-metrics.csv": [
        "name",
        "FanIn",
        "FanOut",
        "LinesOfCode",
        "InstabilityMetric",
        "AbstractnessMetric",
        "PageRank",
    ],
}

ALLOWED_CSV_CONTENT_TYPES = {
    "application/csv",
    "application/octet-stream",
    "application/vnd.ms-excel",
    "text/csv",
    "text/plain",
}


class CSVValidationError(ValueError):
    """Raised when an uploaded file is not a usable CSV dataset."""


@dataclass(frozen=True)
class ValidationReport:
    """Structured validation result for the three analysis datasets."""

    missing_columns: Dict[str, List[str]] = field(default_factory=dict)
    empty_files: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.missing_columns and not self.empty_files

    def api_detail(self) -> dict:
        return {
            "message": "Uploaded CSV files failed validation.",
            "missingColumns": self.missing_columns,
            "emptyFiles": self.empty_files,
        }


def required_columns_for(filename: str) -> List[str]:
    """Return the list of required columns for the given filename."""
    return REQUIRED_COLUMNS[filename]


def missing_required_columns(filename: str, columns: List[str]) -> List[str]:
    """Return any required columns missing from the provided column list."""
    required: Set[str] = set(required_columns_for(filename))
    present: Set[str] = set(columns)
    return [column for column in required_columns_for(filename) if column not in present]


def validate_csv_columns(path: Path, filename: str) -> List[str]:
    """Validate the columns in a CSV file against the expected schema.

    Reads only the header row of the CSV and returns a list of missing required
    columns for the given filename.
    """
    dataframe = pd.read_csv(path, nrows=0)
    return missing_required_columns(filename, list(dataframe.columns))


def validate_upload_type(
    original_name: str | None,
    content_type: str | None,
    field_name: str,
) -> None:
    """Reject uploads that are not named and represented as CSV files."""
    if not original_name or Path(original_name).suffix.lower() != ".csv":
        raise CSVValidationError(f"{field_name} must be a .csv file.")
    if content_type and content_type.lower() not in ALLOWED_CSV_CONTENT_TYPES:
        raise CSVValidationError(
            f"{field_name} has unsupported content type {content_type}."
        )


def validate_csv_file(path: Path, filename: str) -> List[str]:
    """Validate file presence, non-empty rows, parseability, and columns."""
    if not path.is_file() or path.stat().st_size == 0:
        raise CSVValidationError(f"{filename} is empty.")
    try:
        sample = pd.read_csv(path, nrows=1)
    except pd.errors.EmptyDataError as error:
        raise CSVValidationError(f"{filename} is empty.") from error
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        raise CSVValidationError(f"{filename} is not a valid CSV file.") from error
    if sample.empty:
        raise CSVValidationError(f"{filename} contains headers but no data rows.")
    return missing_required_columns(filename, list(sample.columns))


def validate_analysis_data(data: AnalysisData) -> ValidationReport:
    """Validate loaded analysis data and report missing columns per dataset."""
    dataframes: Mapping[str, pd.DataFrame] = {
        "smell-characteristics.csv": data.smell_characteristics,
        "smell-affects.csv": data.smell_affects,
        "component-metrics.csv": data.component_metrics,
    }

    missing_columns = {
        filename: missing_required_columns(filename, list(dataframe.columns))
        for filename, dataframe in dataframes.items()
    }
    empty_files = [
        filename for filename, dataframe in dataframes.items() if dataframe.empty
    ]
    return ValidationReport(
        missing_columns={
            filename: columns
            for filename, columns in missing_columns.items()
            if columns
        },
        empty_files=empty_files,
    )
