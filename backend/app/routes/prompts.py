"""Routes related to prompt version discovery and prompt evaluation retrieval."""

from fastapi import APIRouter


router = APIRouter(prefix="/api", tags=["prompts"])


@router.get("/prompts")
async def list_prompts() -> dict[str, list[str]]:
    """Return a list of available prompt versions for the frontend."""
    return {"promptVersions": []}


@router.get("/prompt-evaluations/{run_id}")
async def get_prompt_evaluations(run_id: str) -> dict[str, str | list[dict]]:
    """Return prompt evaluation results for a given analysis run."""
    return {"runId": run_id, "evaluations": []}
