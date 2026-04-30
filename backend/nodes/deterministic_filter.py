"""Node: deterministic filtering of findings before LLM supervisor.

This node applies rules that should not require an LLM:
- Drop findings below confidence threshold
- Drop findings without file paths
- Drop findings outside changed lines
- Merge exact duplicates by file_path + line_number
- Keep highest-confidence version of duplicates
- Preserve tool-originated findings
"""

from __future__ import annotations

from backend.state import ReviewState


CONFIDENCE_THRESHOLD = 0.6
LINE_PROXIMITY_WINDOW = 3  # allow findings within ±3 lines of a change


def deterministic_filter_node(state: ReviewState) -> dict:
    """Apply deterministic gates to all findings."""
    all_findings = (
        state.get("bug_findings", [])
        + state.get("security_findings", [])
        + state.get("test_findings", [])
    )

    if not all_findings:
        return {"filtered_findings": []}

    filtered = []

    # Get changed lines for relevance check
    parsed_diff = state.get("parsed_diff")
    changed_lines: dict[str, set[int]] = {}
    if parsed_diff:
        changed_lines = parsed_diff.changed_line_numbers

    for finding in all_findings:
        # Drop low confidence
        if finding.confidence < CONFIDENCE_THRESHOLD:
            continue

        # Drop findings without file path
        if not finding.file_path:
            continue

        # Drop findings outside changed lines
        # Allow if: no line_number (repo-level), tool-originated, or nearby
        if finding.line_number is not None and finding.file_path in changed_lines:
            if finding.line_number not in changed_lines[finding.file_path]:
                nearby = any(
                    abs(finding.line_number - cl) <= LINE_PROXIMITY_WINDOW
                    for cl in changed_lines[finding.file_path]
                )
                if not nearby and not finding.is_from_tool:
                    continue

        filtered.append(finding)

    # Deduplicate by file_path + line_number — keep highest confidence
    seen: dict[str, int] = {}
    deduped: list = []

    for finding in filtered:
        key = f"{finding.file_path}:{finding.line_number}"
        if key in seen:
            existing_idx = seen[key]
            if finding.confidence > deduped[existing_idx].confidence:
                deduped[existing_idx] = finding
        else:
            seen[key] = len(deduped)
            deduped.append(finding)

    return {"filtered_findings": deduped}
