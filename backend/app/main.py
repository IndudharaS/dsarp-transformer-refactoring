from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.db.mongo import close_database, initialize_database, ping_database
from app.routes import analyze, prompts, recommendations, reports, stats, upload


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        settings.upload_path.mkdir(parents=True, exist_ok=True)
        settings.report_path.mkdir(parents=True, exist_ok=True)
        await initialize_database()
        app.state.database_ready = True
    except PyMongoError:
        app.state.database_ready = False
    yield
    await close_database()


app = FastAPI(title="DSARP API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(recommendations.router)
app.include_router(stats.router)
app.include_router(prompts.router)
app.include_router(reports.router)


@app.get("/api/health")
async def health() -> dict[str, str | bool]:
    database_ready = False
    try:
        database_ready = await ping_database()
    except PyMongoError:
        database_ready = False

    return {
        "status": "ok",
        "database": database_ready,
    }
