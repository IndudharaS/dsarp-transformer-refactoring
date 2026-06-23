from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from app.db.mongo import get_database, mongo_error_message
from app.pipeline.classifier_client import get_classifier
from app.pipeline.data_loader import load_analysis_data
from app.pipeline.feature_builder import build_smell_objects
from app.pipeline.ranker import rank_recommendations
from app.pipeline.rule_recommender import build_rule_recommendation
from app.pipeline.validator import validate_analysis_data


router = APIRouter(prefix="/api", tags=["analyze"])


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


async def update_run_status(
    run_id: str,
    run_status: str,
    *,
    error_message: str | None = None,
) -> None:
    update: dict[str, Any] = {
        "status": run_status,
        "updatedAt": utc_timestamp(),
    }
    if error_message is None:
        update["error"] = None
    else:
        update["error"] = error_message
    await get_database().analysis_runs.update_one(
        {"runId": run_id},
        {"$set": update},
    )


def build_prediction(
    run_id: str,
    smell: dict[str, Any],
    strategy: str,
    confidence: float,
    model: str,
    created_at: str,
) -> dict[str, Any]:
    return {
        "runId": run_id,
        "smellId": smell["smellId"],
        "modelUsed": model,
        "predictedStrategy": strategy,
        "classifierConfidence": confidence,
        "createdAt": created_at,
    }


def build_recommendation(
    smell: dict[str, Any],
    prediction: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    rule = build_rule_recommendation(smell)
    return {
        "runId": smell["runId"],
        "system": smell["system"],
        "version": smell["version"],
        "smellId": smell["smellId"],
        "smellType": smell["smellType"],
        "affectedElements": smell["affectedElements"],
        "severity": smell["severity"],
        "size": smell["size"],
        "strength": smell["strength"],
        "instabilityGap": smell["instabilityGap"],
        "numberOfEdges": smell["numberOfEdges"],
        "predictedStrategy": prediction["predictedStrategy"],
        "classifierConfidence": prediction["classifierConfidence"],
        "classifierModel": prediction["modelUsed"],
        **rule,
        "promptVersion": "rule-baseline",
        "modelUsed": "rule-based",
        "usedFallback": True,
        "createdAt": created_at,
    }


@router.post("/analyze/{run_id}")
async def analyze_run(run_id: str) -> dict[str, str | int]:
    db = get_database()
    run: dict[str, Any] | None = None

    try:
        run = await db.analysis_runs.find_one({"runId": run_id}, {"_id": 0})
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis run {run_id} was not found.",
            )

        uploaded_files = await db.uploaded_files.find_one(
            {"runId": run_id},
            {"_id": 0},
        )
        if uploaded_files is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Uploaded file metadata for run {run_id} was not found.",
            )

        await update_run_status(run_id, "validating")
        data = load_analysis_data(uploaded_files)
        validation_errors = validate_analysis_data(data)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Uploaded CSV files are missing required columns.",
                    "missingColumns": validation_errors,
                },
            )

        await update_run_status(run_id, "processing")
        smells = build_smell_objects(run, data)
        classifier = get_classifier()
        created_at = utc_timestamp()
        predictions: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        for smell in smells:
            result = classifier.predict(str(smell["smellType"]))
            prediction = build_prediction(
                run_id,
                smell,
                result.strategy,
                result.confidence,
                result.model,
                created_at,
            )
            predictions.append(prediction)
            recommendations.append(
                build_recommendation(smell, prediction, created_at)
            )

        ranked_recommendations = rank_recommendations(recommendations)

        await db.smells.delete_many({"runId": run_id})
        await db.classifier_predictions.delete_many({"runId": run_id})
        await db.recommendations.delete_many({"runId": run_id})

        if smells:
            await db.smells.insert_many(smells)
        if predictions:
            await db.classifier_predictions.insert_many(predictions)
        if ranked_recommendations:
            await db.recommendations.insert_many(ranked_recommendations)

        await db.analysis_runs.update_one(
            {"runId": run_id},
            {
                "$set": {
                    "status": "completed",
                    "totalProcessed": len(smells),
                    "recommendationsGenerated": len(ranked_recommendations),
                    "completedAt": utc_timestamp(),
                    "updatedAt": utc_timestamp(),
                    "error": None,
                }
            },
        )
    except HTTPException as error:
        if run is not None:
            try:
                detail = (
                    error.detail
                    if isinstance(error.detail, str)
                    else error.detail.get("message", "Analysis failed.")
                )
                await update_run_status(run_id, "failed", error_message=detail)
            except PyMongoError:
                pass
        raise
    except (FileNotFoundError, ValueError) as error:
        if run is not None:
            try:
                await update_run_status(
                    run_id,
                    "failed",
                    error_message=str(error),
                )
            except PyMongoError:
                pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except PyMongoError as error:
        if run is not None:
            try:
                await update_run_status(
                    run_id,
                    "failed",
                    error_message=mongo_error_message(error),
                )
            except PyMongoError:
                pass
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error
    except Exception as error:
        if run is not None:
            try:
                await update_run_status(
                    run_id,
                    "failed",
                    error_message="Unexpected analysis error.",
                )
            except PyMongoError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected analysis error.",
        ) from error

    return {
        "runId": run_id,
        "status": "completed",
        "totalProcessed": len(smells),
        "recommendationsGenerated": len(ranked_recommendations),
    }
