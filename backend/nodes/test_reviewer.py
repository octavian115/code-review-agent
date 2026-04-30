"""Node: review diff for missing or inadequate test coverage."""

from __future__ import annotations

from backend.state import ReviewState


def test_reviewer_node(state: ReviewState) -> dict:
    """Review diff for missing or weak tests."""
    # TODO: implement with LLM call
    return {"test_findings": []}
