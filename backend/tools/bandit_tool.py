"""Bandit integration for Python security checks."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from backend.models import ToolResult


SEVERITY_MAP = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
}


def run_bandit(repo_path: str) -> tuple[list[ToolResult], list[str]]:
    """Run bandit recursively and normalize JSON output."""
    path = Path(repo_path).expanduser()
    if not path.exists():
        return [], [f"bandit skipped: repo path does not exist: {repo_path}"]

    try:
        completed = subprocess.run(
            ["bandit", "-r", str(path), "-f", "json"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except FileNotFoundError:
        return [], ["bandit unavailable: install bandit to enable security analysis"]
    except subprocess.TimeoutExpired:
        return [], ["bandit timed out after 45 seconds"]
    except Exception as exc:
        return [], [f"bandit failed: {exc}"]

    if completed.returncode not in (0, 1):
        detail = (completed.stderr or completed.stdout).strip()
        return [], [f"bandit failed with exit code {completed.returncode}: {detail}"]

    stdout = completed.stdout.strip()
    if not stdout:
        return [], []

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [], [f"bandit produced invalid JSON: {exc}"]

    results: list[ToolResult] = []
    for item in payload.get("results", []):
        filename = item.get("filename")
        try:
            file_path = str(Path(filename).resolve().relative_to(path.resolve()))
        except Exception:
            file_path = filename

        severity = SEVERITY_MAP.get(str(item.get("issue_severity", "")).upper(), "medium")
        results.append(
            ToolResult(
                tool="bandit",
                file_path=file_path,
                line_number=item.get("line_number"),
                severity=severity,
                rule_id=item.get("test_id"),
                message=item.get("issue_text") or "bandit finding",
                raw_output=json.dumps(item, sort_keys=True),
            )
        )

    return results, []
