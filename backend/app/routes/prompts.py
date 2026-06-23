from fastapi import APIRouter


router = APIRouter(prefix="/api", tags=["prompts"])


@router.get("/prompts")
async def list_prompts() -> dict[str, list[str]]:
    return {"promptVersions": []}


@router.get("/prompt-evaluations/{run_id}")
async def get_prompt_evaluations(run_id: str) -> dict[str, str | list[dict]]:
    return {"runId": run_id, "evaluations": []}
