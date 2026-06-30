"""Upload routes and helper utilities for the DSARP backend.

This module handles CSV file uploads for smell characteristics, smell affects,
and component metrics. It validates uploaded data, stores metadata in MongoDB,
and exposes endpoints for querying upload runs.
"""

from datetime import datetime, timezone
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.db.mongo import get_database, mongo_error_message
from app.models.schemas import AnalysisRun, UploadResponse, UploadedFilesDocument
from app.pipeline.validator import (
    CSVValidationError,
    validate_csv_file,
    validate_upload_type,
)


router = APIRouter(prefix="/api", tags=["upload"])
settings = get_settings()

FIXED_FILENAMES = {
    "smellCharacteristics": "smell-characteristics.csv",
    "smellAffects": "smell-affects.csv",
    "componentMetrics": "component-metrics.csv",
}

SELECTED_SMELLS = ["godComponent", "unstableDep", "cyclicDep"]


def utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def generate_run_id() -> str:
    """Generate a unique run identifier using timestamp and a random suffix."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid4().hex[:8]}"


async def save_upload(upload_file: UploadFile, destination: Path) -> None:
    """Persist an uploaded file to the configured destination path."""
    try:
        with destination.open("wb") as output:
            while chunk := await upload_file.read(1024 * 1024):
                output.write(chunk)
    finally:
        await upload_file.close()


def stored_path(run_id: str, filename: str) -> str:
    """Return the storage path for a file belonging to a given run."""
    return f"{settings.upload_dir}/{run_id}/{filename}"


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": dict}, 503: {"model": dict}},
)
async def upload_files(
    projectName: str = Form(...),
    systemName: str = Form(...),
    version: str = Form(...),
    smellCharacteristics: UploadFile = File(...),
    smellAffects: UploadFile = File(...),
    componentMetrics: UploadFile = File(...),
) -> UploadResponse:
    """Accept CSV uploads, validate their schema, and record the upload run."""
    if not projectName.strip() or not systemName.strip() or not version.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="projectName, systemName, and version are required.",
        )

    uploads = {
        "smellCharacteristics": smellCharacteristics,
        "smellAffects": smellAffects,
        "componentMetrics": componentMetrics,
    }
    try:
        for key, upload_file in uploads.items():
            validate_upload_type(
                upload_file.filename,
                upload_file.content_type,
                key,
            )
    except CSVValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    run_id = generate_run_id()
    run_dir = settings.upload_path / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    try:
        for key, upload_file in uploads.items():
            await save_upload(upload_file, run_dir / FIXED_FILENAMES[key])

        validation_errors = {}
        for key, filename in FIXED_FILENAMES.items():
            missing_columns = validate_csv_file(run_dir / filename, filename)
            if missing_columns:
                validation_errors[filename] = missing_columns

        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Uploaded CSV files are missing required columns.",
                    "missingColumns": validation_errors,
                },
            )

        now = utc_timestamp()
        analysis_run = AnalysisRun(
            runId=run_id,
            projectName=projectName.strip(),
            systemName=systemName.strip(),
            version=version.strip(),
            status="uploaded",
            selectedSmells=SELECTED_SMELLS,
            createdAt=now,
            updatedAt=now,
        )
        uploaded_files = UploadedFilesDocument(
            runId=run_id,
            files={
                key: {
                    "originalName": upload_file.filename or FIXED_FILENAMES[key],
                    "storedPath": stored_path(run_id, FIXED_FILENAMES[key]),
                }
                for key, upload_file in uploads.items()
            },
            createdAt=now,
        )

        db = get_database()
        await db.analysis_runs.insert_one(analysis_run.model_dump())
        await db.uploaded_files.insert_one(uploaded_files.model_dump())
    except HTTPException:
        shutil.rmtree(run_dir, ignore_errors=True)
        raise
    except (CSVValidationError, ValueError) as error:
        shutil.rmtree(run_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV file: {error}",
        ) from error
    except PyMongoError as error:
        shutil.rmtree(run_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error

    return UploadResponse(
        runId=run_id,
        status="uploaded",
        message="Files uploaded successfully",
    )


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    """Return metadata for a specific upload run, including stored files."""
    try:
        db = get_database()
        run = await db.analysis_runs.find_one({"runId": run_id}, {"_id": 0})
        uploaded_files = await db.uploaded_files.find_one(
            {"runId": run_id},
            {"_id": 0},
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis run {run_id} was not found.",
        )

    return {
        **run,
        "uploadedFiles": uploaded_files,
        "databaseVerified": uploaded_files is not None,
    }


@router.get("/runs")
async def list_runs(limit: int = 20) -> dict:
    """List recent upload runs with optional result limit enforcement."""
    safe_limit = max(1, min(limit, 100))

    try:
        db = get_database()
        runs = await (
            db.analysis_runs.find({}, {"_id": 0})
            .sort("createdAt", -1)
            .limit(safe_limit)
            .to_list(length=safe_limit)
        )
        run_ids = [run["runId"] for run in runs]
        uploaded_file_records = await db.uploaded_files.find(
            {"runId": {"$in": run_ids}},
            {"_id": 0},
        ).to_list(length=safe_limit)
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=mongo_error_message(error),
        ) from error

    files_by_run_id = {
        record["runId"]: record for record in uploaded_file_records
    }
    results = [
        {
            **run,
            "uploadedFiles": files_by_run_id.get(run["runId"]),
            "databaseVerified": run["runId"] in files_by_run_id,
        }
        for run in runs
    ]

    return {"runs": results, "count": len(results)}
