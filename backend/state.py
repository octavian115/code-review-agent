"""
LangGraph state definition for the code review agent.

Separated from models.py so graph.py only imports what it needs for wiring.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from backend.models import Finding, ParsedDiff, ReviewMetadata, ToolResult


class ReviewState(TypedDict):
    """LangGraph state for the code review agent.

    Uses Annotated[list, operator.add] for fields written by parallel nodes
    so findings are safely appended, not overwritten.
    """

    # Input
    raw_diff: str
    repo_path: str | None

    # After parse_diff
    parsed_diff: ParsedDiff | None
    metadata: ReviewMetadata | None

    # After run_static_tools
    tool_results: Annotated[list[ToolResult], operator.add]

    # After parallel reviewers (each appends to its own list)
    bug_findings: Annotated[list[Finding], operator.add]
    security_findings: Annotated[list[Finding], operator.add]
    test_findings: Annotated[list[Finding], operator.add]

    # After deterministic filter
    filtered_findings: list[Finding]

    # After semantic supervisor
    merged_findings: list[Finding]

    # After render
    final_review_markdown: str

    # Error tracking — failures degrade, never crash
    errors: Annotated[list[str], operator.add]
