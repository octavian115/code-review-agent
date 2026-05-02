"""
Core data models for the code review agent.

Design principle: Reviewers emit structured findings, not prose.
The supervisor and renderer work with structured data throughout.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


# ── Diff Models ──────────────────────────────────────────────────────────────


@dataclass
class DiffLine:
    """A single changed line in a diff hunk."""

    line_number: int
    content: str


@dataclass
class Hunk:
    """A contiguous block of changes within a file."""

    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    added_lines: list[DiffLine] = field(default_factory=list)
    removed_lines: list[DiffLine] = field(default_factory=list)
    context_lines: list[DiffLine] = field(default_factory=list)


@dataclass
class ChangedFile:
    """A single file that was modified in the diff."""

    path: str
    status: Literal["added", "modified", "deleted", "renamed"]
    hunks: list[Hunk] = field(default_factory=list)
    old_path: str | None = None  # for renames
    language: str | None = None


@dataclass
class ParsedDiff:
    """Structured representation of a unified diff."""

    files: list[ChangedFile] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def changed_line_numbers(self) -> dict[str, set[int]]:
        """Map of file_path -> set of changed line numbers.
        Used by deterministic filter to drop findings outside changed lines.
        """
        result: dict[str, set[int]] = {}
        for f in self.files:
            lines: set[int] = set()
            for hunk in f.hunks:
                for line in hunk.added_lines:
                    lines.add(line.line_number)
                for line in hunk.removed_lines:
                    lines.add(line.line_number)
            result[f.path] = lines
        return result


# ── Tool Result Model ────────────────────────────────────────────────────────


class ToolResult(BaseModel):
    """Output from a static analysis tool (ruff, bandit, etc.)."""

    tool: Literal["ruff", "bandit", "mypy", "pytest"]
    file_path: str | None = None
    line_number: int | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    message: str
    rule_id: str | None = None
    raw_output: str | None = None


# ── Finding Model ────────────────────────────────────────────────────────────


class Finding(BaseModel):
    """A single review finding emitted by a specialist reviewer.

    This is the central data structure of the system.
    Reviewers produce findings. The supervisor merges them.
    The renderer formats them. Evals score them.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    source: Literal[
        "bug_reviewer",
        "security_reviewer",
        "test_reviewer",
        "ruff",
        "bandit",
        "supervisor",
    ]
    title: str
    description: str
    file_path: str
    line_number: int | None = None
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    recommendation: str
    is_from_tool: bool = False  # True if this finding originated from static analysis


# ── Review Metadata ──────────────────────────────────────────────────────────


class ReviewMetadata(BaseModel):
    """Cheap-to-compute metadata about the diff, useful for supervisor and UI."""

    total_files: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    languages: list[str] = Field(default_factory=list)
    has_repo_path: bool = False
    tools_ran: list[str] = Field(default_factory=list)
    tools_failed: list[str] = Field(default_factory=list)
