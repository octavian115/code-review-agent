"""Node: review diff for security issues."""

from __future__ import annotations

from backend.state import ReviewState


def security_reviewer_node(state: ReviewState) -> dict:
    """Review diff for security issues: auth bypasses, injection, etc."""
    # TODO: implement with LLM call
    return {"security_findings": []}
