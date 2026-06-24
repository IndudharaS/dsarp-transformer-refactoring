"""Routes for generating and downloading analysis reports."""

from fastapi import APIRouter, HTTPException, Query, status


router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports/{run_id}/download")
async def download_report(
    run_id: str,
    format: str = Query(..., pattern="^(csv|excel|html)$"),
) -> dict[str, str]:
    """Return a placeholder response for report downloads.

    Currently report export is not implemented and returns a 501 status.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Report generation for run {run_id} as {format} is not implemented yet.",
    )
