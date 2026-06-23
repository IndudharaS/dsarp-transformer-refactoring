import ast
import json
import math
from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np
import pandas as pd

from app.pipeline.data_loader import AnalysisData


TARGET_SMELLS = {"godComponent", "unstableDep", "cyclicDep"}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
        return bool(result) if isinstance(result, (bool, np.bool_)) else False
    except (TypeError, ValueError):
        return False


def clean_optional_string(value: Any) -> str | None:
    if is_null(value):
        return None
    cleaned = str(value).strip()
    return cleaned or None


def numeric_value(value: Any, default: float = 0.0) -> float:
    if is_null(value) or (isinstance(value, str) and not value.strip()):
        return default
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def integer_value(value: Any) -> int:
    return int(numeric_value(value))


def parse_affected_elements(value: Any) -> list[str]:
    if is_null(value):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]

    raw = str(value).strip()
    if not raw:
        return []

    if raw.startswith("[") and raw.endswith("]"):
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(raw)
                if isinstance(parsed, (list, tuple, set)):
                    return [
                        str(item).strip()
                        for item in parsed
                        if str(item).strip()
                    ]
            except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
                continue

        inner = raw[1:-1].strip()
        if inner:
            elements = [item.strip().strip("\"'") for item in inner.split(",")]
            parsed_elements = [item for item in elements if item]
            if parsed_elements:
                return parsed_elements

    delimiter = ";" if ";" in raw else "," if "," in raw else None
    if delimiter:
        parsed_elements = [item.strip() for item in raw.split(delimiter)]
        return [item for item in parsed_elements if item]

    return [raw]


def json_serializable(value: Any) -> Any:
    if is_null(value):
        return None
    if isinstance(value, dict):
        return {str(key): json_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_serializable(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _component_metric_index(
    component_metrics: pd.DataFrame,
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for _, row in component_metrics.iterrows():
        name = clean_optional_string(row.get("name"))
        if not name:
            continue
        index.setdefault(name, []).append(
            {
            "name": clean_optional_string(row.get("name")),
            "fanIn": numeric_value(row.get("FanIn")),
            "fanOut": numeric_value(row.get("FanOut")),
            "linesOfCode": numeric_value(row.get("LinesOfCode")),
            "instabilityMetric": numeric_value(row.get("InstabilityMetric")),
            "abstractnessMetric": numeric_value(row.get("AbstractnessMetric")),
            "pageRank": numeric_value(row.get("PageRank")),
            }
        )
    return index


def _dependency_index(
    smell_affects: pd.DataFrame,
) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for _, row in smell_affects.iterrows():
        from_component = clean_optional_string(row.get("from"))
        to_component = clean_optional_string(row.get("to"))
        if not from_component or not to_component:
            continue
        dependency = {"from": from_component, "to": to_component}
        index.setdefault(from_component, []).append(dependency)
        if to_component != from_component:
            index.setdefault(to_component, []).append(dependency)
    return index


def _matching_component_metrics(
    affected_elements: list[str],
    metric_index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    return [
        metric
        for element in affected_elements
        for metric in metric_index.get(element, [])
    ]


def _matching_dependencies(
    affected_elements: list[str],
    dependency_index: dict[str, list[dict[str, str]]],
) -> list[dict[str, str]]:
    dependencies: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for element in affected_elements:
        for dependency in dependency_index.get(element, []):
            edge = (dependency["from"], dependency["to"])
            if edge not in seen:
                dependencies.append(dependency)
                seen.add(edge)
    return dependencies


def _system_column(columns: Iterable[str]) -> str | None:
    lookup = {column.lower(): column for column in columns}
    return lookup.get("system")


def build_smell_objects(
    run: dict[str, Any],
    data: AnalysisData,
) -> list[dict[str, Any]]:
    smells = data.smell_characteristics.copy()
    smells = smells[smells["smellType"].isin(TARGET_SMELLS)]

    system_column = _system_column(smells.columns)
    if system_column:
        selected_system = str(run["systemName"]).strip().casefold()
        smells = smells[
            smells[system_column]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
            .eq(selected_system)
        ]

    created_at = utc_timestamp()
    metric_index = _component_metric_index(data.component_metrics)
    dependency_index = _dependency_index(data.smell_affects)
    smell_objects: list[dict[str, Any]] = []
    for position, (_, row) in enumerate(smells.iterrows(), start=1):
        affected_elements = parse_affected_elements(row.get("AffectedElements"))
        smell_objects.append(
            {
                "runId": run["runId"],
                "smellId": f"S{position:03d}",
                "system": run["systemName"],
                "version": run["version"],
                "smellType": clean_optional_string(row.get("smellType")),
                "affectedElements": affected_elements,
                "severity": numeric_value(row.get("Severity")),
                "size": numeric_value(row.get("Size")),
                "strength": numeric_value(row.get("Strength")),
                "instabilityGap": numeric_value(row.get("InstabilityGap")),
                "numberOfEdges": integer_value(row.get("NumberOfEdges")),
                "shape": clean_optional_string(row.get("Shape")),
                "centralComponent": clean_optional_string(
                    row.get("CentralComponent")
                ),
                "componentMetrics": _matching_component_metrics(
                    affected_elements,
                    metric_index,
                ),
                "dependencies": _matching_dependencies(
                    affected_elements,
                    dependency_index,
                ),
                "createdAt": created_at,
            }
        )
    return json_serializable(smell_objects)
