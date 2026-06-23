from typing import Any


PRIORITY_FIELDS = {
    "severity": 0.35,
    "size": 0.20,
    "strength": 0.20,
    "instabilityGap": 0.15,
    "numberOfEdges": 0.10,
}


def _normalized_values(
    records: list[dict[str, Any]],
    field: str,
) -> list[float]:
    values = [float(record.get(field, 0.0)) for record in records]
    if not values:
        return []
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        return [0.5] * len(values)
    return [(value - minimum) / (maximum - minimum) for value in values]


def recommendation_quality_score(confidence: float) -> float:
    score = (
        0.25 * 1.0
        + 0.20 * confidence
        + 0.20 * 1.0
        + 0.15 * 0.8
        + 0.10 * 0.8
        + 0.10 * 0.8
    )
    return round(score, 6)


def rank_level(score: float) -> str:
    if score >= 0.80:
        return "Critical"
    if score >= 0.60:
        return "High"
    if score >= 0.40:
        return "Medium"
    return "Low"


def rank_recommendations(
    recommendations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized_by_field = {
        field: _normalized_values(recommendations, field)
        for field in PRIORITY_FIELDS
    }

    for index, recommendation in enumerate(recommendations):
        priority_score = sum(
            weight * normalized_by_field[field][index]
            for field, weight in PRIORITY_FIELDS.items()
        )
        quality_score = recommendation_quality_score(
            float(recommendation["recommendationConfidence"])
        )
        final_score = (
            0.50 * priority_score
            + 0.30 * quality_score
            + 0.20 * float(recommendation["classifierConfidence"])
        )
        recommendation["smellPriorityScore"] = round(priority_score, 6)
        recommendation["recommendationQualityScore"] = quality_score
        recommendation["finalRankingScore"] = round(final_score, 6)
        recommendation["rankLevel"] = rank_level(final_score)

    recommendations.sort(
        key=lambda item: item["finalRankingScore"],
        reverse=True,
    )
    for position, recommendation in enumerate(recommendations, start=1):
        recommendation["rankPosition"] = position
    return recommendations
