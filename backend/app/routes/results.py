"""Processed smell and transformer-training dataset retrieval routes."""

import csv
from io import StringIO

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pymongo.errors import PyMongoError

from app.db.mongo import get_database, mongo_error_message


router = APIRouter(prefix="/api", tags=["results"])


async def ensure_run_exists(run_id: str) -> None:
    run = await get_database().analysis_runs.find_one(
        {"runId": run_id},
        {"_id": 1},
    )
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis run {run_id} was not found.",
        )


@router.get("/smells/{run_id}")
async def list_processed_smells(
    run_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Return paginated normalized smell objects for a run."""
    try:
        await ensure_run_exists(run_id)
        db = get_database()
        total = await db.smells.count_documents({"runId": run_id})
        smells = await (
            db.smells.find({"runId": run_id}, {"_id": 0})
            .sort("smellId", 1)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error
    return {"runId": run_id, "smells": smells, "count": len(smells), "total": total}


@router.get("/training-data/{run_id}")
async def get_training_data(run_id: str) -> dict:
    """Return Stage 2 transformer features as JSON."""
    try:
        await ensure_run_exists(run_id)
        features = await (
            get_database()
            .training_features.find({"runId": run_id}, {"_id": 0})
            .sort("smellId", 1)
            .to_list(length=None)
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error
    if not features:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No training data exists. Complete analysis for this run first.",
        )
    return {"runId": run_id, "features": features, "count": len(features)}


@router.get("/training-data/{run_id}/export")
async def export_training_data(run_id: str) -> StreamingResponse:
    """Export exactly two CSV columns, text and label, for Google Colab."""
    payload = await get_training_data(run_id)
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["text", "label"])
    writer.writeheader()
    writer.writerows(
        {"text": feature["text"], "label": feature["label"]}
        for feature in payload["features"]
    )
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="dsarp-training-{run_id}.csv"'
    )
    return response
