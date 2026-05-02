"""Ruff integration.

The wrapper returns normalized ToolResult objects and never raises for normal
tool failures. Missing binaries, invalid repos, and non-zero lint exits are all
represented as data so the graph can continue.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.models import ToolResult


def run_ruff(repo_path: str) -> tuple[list[ToolResult], list[str]]:
    """Run ruff against a repository and normalize JSON output."""
    path = Path(repo_path).expanduser()
    if not path.exists():
        return [], [f"ruff skipped: repo path does not exist: {repo_path}"]

    try:
        completed = subprocess.run(
            ["ruff", "check", str(path), "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        return [], ["ruff unavailable: install ruff to enable lint analysis"]
    except subprocess.TimeoutExpired:
        return [], ["ruff timed out after 30 seconds"]
    except Exception as exc:
        return [], [f"ruff failed: {exc}"]

    if completed.returncode not in (0, 1):
        detail = (completed.stderr or completed.stdout).strip()
        return [], [f"ruff failed with exit code {completed.returncode}: {detail}"]

    stdout = completed.stdout.strip()
    if not stdout:
        return [], []

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [], [f"ruff produced invalid JSON: {exc}"]

    results: list[ToolResult] = []
    for item in payload:
        filename = item.get("filename")
        try:
            file_path = str(Path(filename).resolve().relative_to(path.resolve()))
        except Exception:
            file_path = filename

        location = item.get("location") or {}
        results.append(
            ToolResult(
                tool="ruff",
                file_path=file_path,
                line_number=location.get("row"),
                severity="medium",
                rule_id=item.get("code"),
                message=item.get("message") or "ruff finding",
                raw_output=json.dumps(item, sort_keys=True),
            )
        )

    return results, []
