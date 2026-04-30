"""Node: parse raw diff into structured data and compute metadata."""

from __future__ import annotations

from backend.diff_parser import parse_diff
from backend.models import ReviewMetadata
from backend.state import ReviewState


def parse_diff_node(state: ReviewState) -> dict:
    """Parse raw diff into structured data and compute metadata."""
    raw_diff = state["raw_diff"]

    try:
        parsed = parse_diff(raw_diff)
    except Exception as e:
        return {
            "parsed_diff": None,
            "metadata": ReviewMetadata(),
            "errors": [f"Diff parsing failed: {e}"],
        }

    languages = list(
        {f.language for f in parsed.files if f.language is not None}
    )

    metadata = ReviewMetadata(
        total_files=parsed.total_files,
        total_additions=parsed.total_additions,
        total_deletions=parsed.total_deletions,
        languages=languages,
        has_repo_path=state.get("repo_path") is not None,
    )

    return {
        "parsed_diff": parsed,
        "metadata": metadata,
    }
