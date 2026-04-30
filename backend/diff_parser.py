"""
Diff parser: converts a raw unified diff string into structured ParsedDiff.

Handles standard unified diff format (git diff / diff -u output).
Does not require git or any external tools.
"""

from __future__ import annotations

import re
from pathlib import Path

from backend.models import ChangedFile, DiffLine, Hunk, ParsedDiff

# Regex patterns for unified diff parsing
FILE_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$")
OLD_FILE_RE = re.compile(r"^--- (?:a/)?(.+)$")
NEW_FILE_RE = re.compile(r"^\+\+\+ (?:b/)?(.+)$")
HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

# Language detection by extension
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".sql": "sql",
    ".sh": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
}


def detect_language(file_path: str) -> str | None:
    """Detect programming language from file extension."""
    suffix = Path(file_path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(suffix)


def detect_file_status(old_path: str, new_path: str) -> str:
    """Determine if a file was added, deleted, modified, or renamed."""
    if old_path == "/dev/null":
        return "added"
    if new_path == "/dev/null":
        return "deleted"
    if old_path != new_path:
        return "renamed"
    return "modified"


def parse_diff(raw_diff: str) -> ParsedDiff:
    """Parse a unified diff string into a structured ParsedDiff object.

    Supports standard git diff output format:
        diff --git a/file.py b/file.py
        --- a/file.py
        +++ b/file.py
        @@ -10,7 +10,7 @@
        -old line
        +new line
         context line
    """
    lines = raw_diff.split("\n")
    files: list[ChangedFile] = []
    total_additions = 0
    total_deletions = 0

    current_file: ChangedFile | None = None
    current_hunk: Hunk | None = None
    old_path: str | None = None
    new_path: str | None = None

    # Track line numbers within current hunk
    current_new_line = 0
    current_old_line = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # ── File header ──────────────────────────────────────────────
        file_match = FILE_HEADER_RE.match(line)
        if file_match:
            # Save previous file if exists
            if current_file is not None:
                if current_hunk is not None:
                    current_file.hunks.append(current_hunk)
                files.append(current_file)

            old_path = file_match.group(1)
            new_path = file_match.group(2)
            current_file = None
            current_hunk = None
            i += 1
            continue

        # ── Old file path ────────────────────────────────────────────
        old_match = OLD_FILE_RE.match(line)
        if old_match and old_path is not None:
            old_path = old_match.group(1)
            i += 1
            continue

        # ── New file path ────────────────────────────────────────────
        new_match = NEW_FILE_RE.match(line)
        if new_match and old_path is not None:
            new_path = new_match.group(1)
            status = detect_file_status(old_path, new_path)
            file_path = new_path if status != "deleted" else old_path
            current_file = ChangedFile(
                path=file_path,
                status=status,
                old_path=old_path if status == "renamed" else None,
                language=detect_language(file_path),
            )
            i += 1
            continue

        # ── Hunk header ──────────────────────────────────────────────
        hunk_match = HUNK_HEADER_RE.match(line)
        if hunk_match and current_file is not None:
            # Save previous hunk
            if current_hunk is not None:
                current_file.hunks.append(current_hunk)

            old_start = int(hunk_match.group(1))
            old_lines = int(hunk_match.group(2) or "1")
            new_start = int(hunk_match.group(3))
            new_lines = int(hunk_match.group(4) or "1")

            current_hunk = Hunk(
                old_start=old_start,
                old_lines=old_lines,
                new_start=new_start,
                new_lines=new_lines,
            )
            current_old_line = old_start
            current_new_line = new_start
            i += 1
            continue

        # ── Diff content lines ───────────────────────────────────────
        if current_hunk is not None:
            if line.startswith("+"):
                content = line[1:]
                current_hunk.added_lines.append(
                    DiffLine(line_number=current_new_line, content=content)
                )
                current_new_line += 1
                total_additions += 1
            elif line.startswith("-"):
                content = line[1:]
                current_hunk.removed_lines.append(
                    DiffLine(line_number=current_old_line, content=content)
                )
                current_old_line += 1
                total_deletions += 1
            elif line.startswith(" "):
                content = line[1:]
                current_hunk.context_lines.append(
                    DiffLine(line_number=current_new_line, content=content)
                )
                current_new_line += 1
                current_old_line += 1

        i += 1

    # Save last file and hunk
    if current_file is not None:
        if current_hunk is not None:
            current_file.hunks.append(current_hunk)
        files.append(current_file)

    return ParsedDiff(
        files=files,
        total_additions=total_additions,
        total_deletions=total_deletions,
    )
