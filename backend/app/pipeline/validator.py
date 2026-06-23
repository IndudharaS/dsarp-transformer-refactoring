from pathlib import Path
from typing import Dict, List, Mapping, Set

import pandas as pd

from app.pipeline.data_loader import AnalysisData


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
    return REQUIRED_COLUMNS[filename]


def missing_required_columns(filename: str, columns: List[str]) -> List[str]:
    required: Set[str] = set(required_columns_for(filename))
    present: Set[str] = set(columns)
    return [column for column in required_columns_for(filename) if column not in present]


def validate_csv_columns(path: Path, filename: str) -> List[str]:
    dataframe = pd.read_csv(path, nrows=0)
    return missing_required_columns(filename, list(dataframe.columns))


def validate_analysis_data(data: AnalysisData) -> Dict[str, List[str]]:
    dataframes: Mapping[str, pd.DataFrame] = {
        "smell-characteristics.csv": data.smell_characteristics,
        "smell-affects.csv": data.smell_affects,
        "component-metrics.csv": data.component_metrics,
    }
    errors = {
        filename: missing_required_columns(filename, list(dataframe.columns))
        for filename, dataframe in dataframes.items()
    }
    return {filename: columns for filename, columns in errors.items() if columns}
