from typing import Dict, List

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    runId: str
    status: str
    message: str


class AnalysisRun(BaseModel):
    runId: str
    projectName: str
    systemName: str
    version: str
    status: str
    selectedSmells: List[str] = Field(default_factory=list)
    createdAt: str
    updatedAt: str


class StoredFileMetadata(BaseModel):
    originalName: str
    storedPath: str


class UploadedFilesDocument(BaseModel):
    runId: str
    files: Dict[str, StoredFileMetadata]
    createdAt: str


class ErrorResponse(BaseModel):
    detail: str
