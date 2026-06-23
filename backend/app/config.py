from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel

import os


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db: str = os.getenv("MONGO_DB", "dsarp")
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    report_dir: str = os.getenv("REPORT_DIR", "reports")
    hpc_llm_base_url: str = os.getenv("HPC_LLM_BASE_URL", "http://localhost:9000/v1")
    hpc_llm_model: str = os.getenv(
        "HPC_LLM_MODEL",
        "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
    )
    cors_origins: List[str] = ["http://localhost:3000"]

    @property
    def base_path(self) -> Path:
        return BASE_DIR

    @property
    def upload_path(self) -> Path:
        return BASE_DIR / self.upload_dir

    @property
    def report_path(self) -> Path:
        return BASE_DIR / self.report_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()
