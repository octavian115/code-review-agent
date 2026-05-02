"""Node: run static analysis tools (ruff, bandit) against the repo."""

from __future__ import annotations

from backend.models import ReviewMetadata
from backend.state import ReviewState
from backend.tools.bandit_tool import run_bandit
from backend.tools.ruff_tool import run_ruff


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

    results = []
    errors = []
    tools_ran = []
    tools_failed = []

    for tool_name, runner in (("ruff", run_ruff), ("bandit", run_bandit)):
        tool_results, tool_errors = runner(repo_path)
        if tool_errors:
            tools_failed.append(tool_name)
            errors.extend(tool_errors)
        else:
            tools_ran.append(tool_name)
        results.extend(tool_results)

    metadata = state.get("metadata")
    if metadata is not None:
        metadata = metadata.model_copy(
            update={
                "tools_ran": sorted(set(metadata.tools_ran + tools_ran)),
                "tools_failed": sorted(set(metadata.tools_failed + tools_failed)),
            }
        )
    else:
        metadata = ReviewMetadata(
            has_repo_path=True,
            tools_ran=sorted(set(tools_ran)),
            tools_failed=sorted(set(tools_failed)),
        )

    return {
        "tool_results": results,
        "metadata": metadata,
        "errors": errors,
    }
