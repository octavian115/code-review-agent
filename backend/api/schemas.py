"""FastAPI request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models import Finding, ReviewMetadata, ToolResult


class ReviewRequest(BaseModel):
    raw_diff: str = Field(min_length=1)
    repo_path: str | None = None


class ReviewResponse(BaseModel):
    findings: list[Finding]
    markdown: str
    tool_results: list[ToolResult]
    metadata: ReviewMetadata | None
    errors: list[str]
