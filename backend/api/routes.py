"""HTTP routes for the code review agent."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas import ReviewRequest, ReviewResponse
from backend.graph import build_graph
from backend.state import ReviewState

router = APIRouter()


def initial_state(request: ReviewRequest) -> ReviewState:
    return {
        "raw_diff": request.raw_diff,
        "repo_path": request.repo_path,
        "parsed_diff": None,
        "metadata": None,
        "tool_results": [],
        "bug_findings": [],
        "security_findings": [],
        "test_findings": [],
        "filtered_findings": [],
        "merged_findings": [],
        "final_review_markdown": "",
        "errors": [],
    }


@router.post("/review", response_model=ReviewResponse)
def review_diff(request: ReviewRequest) -> ReviewResponse:
    graph = build_graph()
    final = graph.invoke(initial_state(request))
    return ReviewResponse(
        findings=final.get("merged_findings", []),
        markdown=final.get("final_review_markdown", ""),
        tool_results=final.get("tool_results", []),
        metadata=final.get("metadata"),
        errors=final.get("errors", []),
    )
