"""Node: LLM-powered semantic deduplication and final consolidation.

Handles what deterministic filter cannot:
- Are two findings about different files actually the same issue?
- Is this finding worth blocking a merge?
- Which explanation is clearer?
"""

from __future__ import annotations

from backend.state import ReviewState


def semantic_supervisor_node(state: ReviewState) -> dict:
    """Semantic deduplication and consolidation of findings."""
    filtered = state.get("filtered_findings", [])

    if not filtered:
        return {"merged_findings": []}

    # TODO: implement with LLM call
    # For now, pass through filtered findings
    return {"merged_findings": filtered}
