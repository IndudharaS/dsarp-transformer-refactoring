"""MongoDB setup and utility helpers.

This module is responsible for configuring the MongoDB connection, ensuring required
collections and indexes exist, seeding known software system metadata, and exposing
database helper functions used by the application.
"""

from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config import get_settings


# Collections that should exist in the database for application operations.
COLLECTIONS: List[str] = [
    "software_systems",
    "analysis_runs",
    "uploaded_files",
    "smells",
    "classifier_predictions",
    "prompt_versions",
    "prompt_evaluations",
    "model_outputs",
    "recommendations",
    "reports",
]


# Default supported software systems seeded into the database.
SUPPORTED_SOFTWARE_SYSTEMS: List[Dict[str, Any]] = [
    {
        "name": "Tika",
        "version": "697d7c047daf1f661a4ed067bbc8f9c58bb6faa2",
        "files": 1813,
    },
    {
        "name": "Karaf",
        "version": "5f5677d7395170208907f2f1655ae9fd9b3bff9e",
        "files": 16892,
    },
    {
        "name": "Struts",
        "version": "d59aea5f5d6099ba09e894cb8810e00a37e112b1",
        "files": 2462,
    },
    {
        "name": "Logging-Log4j2",
        "version": "4f474b32751f4ccad67424ca585612584440cd63",
        "files": 3283,
    },
    {
        "name": "Cassandra",
        "version": "0269fd5665751e8a6d8eab852e0f66c142b10ee6",
        "files": 4675,
    },
]


# Load application settings from configuration.
settings = get_settings()

# Create the MongoDB client with a short server selection timeout.
client: AsyncIOMotorClient = AsyncIOMotorClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=3000,
)

# Reference the configured database for application use.
database: AsyncIOMotorDatabase = client[settings.mongo_db]


def get_database() -> AsyncIOMotorDatabase:
    """Return the shared MongoDB database instance."""
    # The global database object is created once and reused by all callers.
    return database


async def ping_database() -> bool:
    """Ping the MongoDB server to confirm the connection is healthy."""
    # Use the MongoDB ping command to validate connectivity and server availability.
    await database.command("ping")
    return True


async def initialize_database() -> None:
    """Initialize the database schema and seed required data.

    This creates any missing collections, ensures the expected indexes exist,
    and upserts the supported software systems into the software_systems collection.
    """
    existing_collections = await database.list_collection_names()
    for collection_name in COLLECTIONS:
        if collection_name not in existing_collections:
            # Create any collection that does not already exist.
            await database.create_collection(collection_name)

    # Create required indexes for unique constraints and query performance.
    await database.analysis_runs.create_index("runId", unique=True)
    await database.uploaded_files.create_index("runId", unique=True)
    await database.software_systems.create_index("name", unique=True)
    await database.smells.create_index([("runId", 1), ("smellId", 1)], unique=True)
    await database.classifier_predictions.create_index(
        [("runId", 1), ("smellId", 1)],
        unique=True,
    )
    await database.recommendations.create_index(
        [("runId", 1), ("smellId", 1)],
        unique=True,
    )
    await database.recommendations.create_index(
        [("runId", 1), ("rankPosition", 1)]
    )

    # Seed the supported software systems data.
    for system in SUPPORTED_SOFTWARE_SYSTEMS:
        await database.software_systems.update_one(
            {"name": system["name"]},
            {"$set": system},
            upsert=True,
        )


async def close_database() -> None:
    """Close the MongoDB client connection."""
    # Close the underlying client connection when the application shuts down.
    client.close()


def mongo_error_message(error: PyMongoError) -> str:
    """Format a readable message for MongoDB-related exceptions."""
    # Convert a PyMongo exception into a simpler message for logging or responses.
    return f"MongoDB operation failed: {error.__class__.__name__}"
