from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config import get_settings


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


settings = get_settings()
client: AsyncIOMotorClient = AsyncIOMotorClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=3000,
)
database: AsyncIOMotorDatabase = client[settings.mongo_db]


def get_database() -> AsyncIOMotorDatabase:
    return database


async def ping_database() -> bool:
    await database.command("ping")
    return True


async def initialize_database() -> None:
    existing_collections = await database.list_collection_names()
    for collection_name in COLLECTIONS:
        if collection_name not in existing_collections:
            await database.create_collection(collection_name)

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

    for system in SUPPORTED_SOFTWARE_SYSTEMS:
        await database.software_systems.update_one(
            {"name": system["name"]},
            {"$set": system},
            upsert=True,
        )


async def close_database() -> None:
    client.close()


def mongo_error_message(error: PyMongoError) -> str:
    return f"MongoDB operation failed: {error.__class__.__name__}"
