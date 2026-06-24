"""Pydantic schema definitions for API request and response payloads."""

from typing import Dict, List

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response payload returned after a file upload or analysis request."""

    runId: str
    status: str
    message: str


class AnalysisRun(BaseModel):
    """Represents an analysis run record stored in the system."""

    runId: str
    projectName: str
    systemName: str
    version: str
    status: str
    selectedSmells: List[str] = Field(default_factory=list)
    createdAt: str
    updatedAt: str


class StoredFileMetadata(BaseModel):
    """Metadata for a file uploaded as part of an analysis run."""

    originalName: str
    storedPath: str


class UploadedFilesDocument(BaseModel):
    """Document structure for uploaded file metadata associated with a run."""

    runId: str
    files: Dict[str, StoredFileMetadata]
    createdAt: str


class ErrorResponse(BaseModel):
    """Standard error response payload used by API endpoints."""

    detail: str
