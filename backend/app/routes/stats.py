"""Routes that aggregate statistics for analysis runs and recommendation outputs."""

from collections import Counter, defaultdict
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from app.db.mongo import get_database, mongo_error_message


router = APIRouter(prefix="/api", tags=["stats"])


def average_severity_by_type(
    recommendations: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute average severity values grouped by smell type."""
    severities: dict[str, list[float]] = defaultdict(list)
    for recommendation in recommendations:
        severities[str(recommendation["smellType"])].append(
            float(recommendation.get("severity", 0.0))
        )
    return {
        smell_type: round(sum(values) / len(values), 6)
        for smell_type, values in severities.items()
    }


@router.get("/stats/{run_id}")
async def get_stats(run_id: str) -> dict:
    """Return summary statistics for a specific analysis run."""
    try:
        db = get_database()
        run = await db.analysis_runs.find_one({"runId": run_id}, {"_id": 0})
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis run {run_id} was not found.",
            )

        recommendations = await (
            db.recommendations.find({"runId": run_id}, {"_id": 0})
            .sort("rankPosition", 1)
            .to_list(length=None)
        )

        # Count the number of smells that were processed for the run.
        total_smells = await db.smells.count_documents({"runId": run_id})
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error

    return {
        "runId": run_id,
        "system": run["systemName"],
        "totalSmellsProcessed": total_smells,
        "recommendationsGenerated": len(recommendations),
        "smellsByType": dict(
            Counter(item["smellType"] for item in recommendations)
        ),
        "predictedStrategies": dict(
            Counter(item["predictedStrategy"] for item in recommendations)
        ),
        "priorityDistribution": dict(
            Counter(item["rankLevel"] for item in recommendations)
        ),
        "riskDistribution": dict(
            Counter(item["risk"] for item in recommendations)
        ),
        "averageSeverityBySmellType": average_severity_by_type(recommendations),
        "topRecommendations": recommendations[:10],
    }
