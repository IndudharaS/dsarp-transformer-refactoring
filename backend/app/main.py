"""Application entry point for the DSARP FastAPI service.

This module configures the FastAPI application, middleware, route inclusion,
and application lifecycle handling for database initialization and cleanup.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.db.mongo import close_database, initialize_database, ping_database
from app.routes import analyze, prompts, recommendations, reports, stats, upload


# Load application settings from configuration.
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown behavior.

    On startup, ensure required directories exist and initialize the database.
    On shutdown, close the MongoDB client connection.
    """
    try:
        settings.upload_path.mkdir(parents=True, exist_ok=True)
        settings.report_path.mkdir(parents=True, exist_ok=True)
        await initialize_database()
        app.state.database_ready = True
    except PyMongoError:
        # If database initialization fails, record that the database is unavailable.
        app.state.database_ready = False

    yield

    # Close the database connection during application shutdown.
    await close_database()


# Create the FastAPI application with the custom lifespan handler.
# The lifespan callback manages startup and shutdown tasks such as directory
# creation and database setup/cleanup.
app = FastAPI(title="DSARP API", version="0.1.0", lifespan=lifespan)

# Configure CORS middleware using settings from the application configuration.
# This allows the frontend to communicate with the backend from allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers that expose functional API endpoints for uploads, analysis,
# recommendations, statistics, prompts, and reports.
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(recommendations.router)
app.include_router(stats.router)
app.include_router(prompts.router)
app.include_router(reports.router)


@app.get("/api/health")
async def health() -> dict[str, str | bool]:
    """Return the health status of the application and database connection."""
    database_ready = False

    try:
        database_ready = await ping_database()
    except PyMongoError:
        # If the database ping fails, indicate the database is unavailable.
        database_ready = False

    return {
        "status": "ok",
        "database": database_ready,
    }
