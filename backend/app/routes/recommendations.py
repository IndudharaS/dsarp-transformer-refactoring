"""API routes for retrieving saved recommendations from analysis runs."""

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from app.db.mongo import get_database, mongo_error_message


router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommendations/{run_id}")
async def list_recommendations(run_id: str) -> dict:
    """Return the ranked recommendations for a previously completed run."""
    try:
        db = get_database()
        run = await db.analysis_runs.find_one({"runId": run_id}, {"_id": 0})
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis run {run_id} was not found.",
            )

        # Load all recommendations for the given run and preserve rank order.
        recommendations = await (
            db.recommendations.find({"runId": run_id}, {"_id": 0})
            .sort("rankPosition", 1)
            .to_list(length=None)
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error

    return {
        "runId": run_id,
        "status": run.get("status"),
        "recommendations": recommendations,
        "count": len(recommendations),
    }


@router.get("/recommendations/{run_id}/{smell_id}")
async def get_recommendation(run_id: str, smell_id: str) -> dict:
    """Return a single recommendation for a smell in the specified run."""
    try:
        recommendation = await get_database().recommendations.find_one(
            {"runId": run_id, "smellId": smell_id},
            {"_id": 0},
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Recommendation for smell {smell_id} in run {run_id} "
                "was not found."
            ),
        )

    return recommendation
