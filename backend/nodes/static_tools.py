"""Node: run static analysis tools (ruff, bandit) against the repo."""

from __future__ import annotations

from backend.state import ReviewState


def run_static_tools_node(state: ReviewState) -> dict:
    """Run ruff and bandit against the repo if a path is available.

    If no repo_path is provided, returns empty results — reviewers
    will reason from the diff alone.
    """
    repo_path = state.get("repo_path")

    if not repo_path:
        return {
            "tool_results": [],
            "errors": [],
        }

    # TODO: implement ruff and bandit execution
    return {
        "tool_results": [],
        "errors": [],
    }
