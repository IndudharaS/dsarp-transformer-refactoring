"""Validators for uploaded analysis CSV datasets.

This module defines the expected CSV schema for each uploaded analysis file and
provides helper functions that check for missing required columns in both file
paths and loaded pandas DataFrames.
"""

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


def validate_analysis_data(data: AnalysisData) -> Dict[str, List[str]]:
    """Validate loaded analysis data and report missing columns per dataset."""
    dataframes: Mapping[str, pd.DataFrame] = {
        "smell-characteristics.csv": data.smell_characteristics,
        "smell-affects.csv": data.smell_affects,
        "component-metrics.csv": data.component_metrics,
    }

    errors = {
        filename: missing_required_columns(filename, list(dataframe.columns))
        for filename, dataframe in dataframes.items()
    }
    # Return only files that are missing columns.
    return {filename: columns for filename, columns in errors.items() if columns}
