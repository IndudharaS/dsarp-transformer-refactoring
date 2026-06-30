"""HTTP-level tests for Stage 2 validation and result retrieval routes."""

import csv
from io import StringIO
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app as full_app
from app.routes import results, upload


class FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def sort(self, *_args) -> "FakeCursor":
        return self

    def skip(self, count: int) -> "FakeCursor":
        self.documents = self.documents[count:]
        return self

    def limit(self, count: int) -> "FakeCursor":
        self.documents = self.documents[:count]
        return self

    async def to_list(self, length=None) -> list[dict]:
        return self.documents if length is None else self.documents[:length]


class FakeCollection:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    async def find_one(self, *_args, **_kwargs) -> dict | None:
        return self.documents[0] if self.documents else None

    def find(self, *_args, **_kwargs) -> FakeCursor:
        return FakeCursor([dict(document) for document in self.documents])

    async def count_documents(self, *_args, **_kwargs) -> int:
        return len(self.documents)


class FakeDatabase:
    def __init__(self) -> None:
        self.analysis_runs = FakeCollection([{"_id": "run", "runId": "run-1"}])
        self.smells = FakeCollection(
            [{"runId": "run-1", "smellId": "S001", "smellType": "cyclicDep"}]
        )
        self.training_features = FakeCollection(
            [
                {
                    "runId": "run-1",
                    "smellId": "S001",
                    "text": "Architectural smell: cyclicDep, components A and B.",
                    "label": "ExtractSharedComponent",
                }
            ]
        )


class Stage2ApiTests(unittest.TestCase):
    def test_stage2_paths_are_registered(self) -> None:
        paths = full_app.openapi()["paths"]
        expected = {
            "/api/upload",
            "/api/analyze/{run_id}",
            "/api/smells/{run_id}",
            "/api/recommendations/{run_id}",
            "/api/recommendations/{run_id}/{smell_id}",
            "/api/stats/{run_id}",
            "/api/training-data/{run_id}",
            "/api/training-data/{run_id}/export",
        }
        self.assertTrue(expected.issubset(paths))

    def test_upload_rejects_invalid_extension(self) -> None:
        test_app = FastAPI()
        test_app.include_router(upload.router)
        client = TestClient(test_app)
        valid_csv = b"name,FanIn,FanOut,LinesOfCode,InstabilityMetric,AbstractnessMetric,PageRank\nA,1,1,10,0.5,0.2,0.1\n"
        response = client.post(
            "/api/upload",
            data={"projectName": "Test", "systemName": "Tika", "version": "v1"},
            files={
                "smellCharacteristics": ("smells.json", b"{}", "application/json"),
                "smellAffects": ("affects.csv", b"from,to,fromId,toId\nA,B,1,2\n", "text/csv"),
                "componentMetrics": ("metrics.csv", valid_csv, "text/csv"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("must be a .csv", response.json()["detail"])

    def test_processed_results_and_training_export(self) -> None:
        test_app = FastAPI()
        test_app.include_router(results.router)
        client = TestClient(test_app)
        fake_database = FakeDatabase()
        with patch("app.routes.results.get_database", return_value=fake_database):
            smells = client.get("/api/smells/run-1")
            training = client.get("/api/training-data/run-1")
            exported = client.get("/api/training-data/run-1/export")

        self.assertEqual(smells.status_code, 200)
        self.assertEqual(smells.json()["total"], 1)
        self.assertEqual(training.status_code, 200)
        self.assertEqual(training.json()["features"][0]["label"], "ExtractSharedComponent")
        rows = list(csv.DictReader(StringIO(exported.text)))
        self.assertEqual(list(rows[0]), ["text", "label"])
        self.assertEqual(rows[0]["label"], "ExtractSharedComponent")


if __name__ == "__main__":
    unittest.main()
