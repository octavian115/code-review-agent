"""Small deterministic reviewer helpers.

These heuristics are intentionally conservative. They provide a no-LLM baseline
for evals and demos, while the node boundaries still allow LLM reviewers to be
plugged in later.
"""

from __future__ import annotations

from backend.models import ChangedFile, DiffLine, ParsedDiff


def added_text(file: ChangedFile) -> str:
    return "\n".join(line.content for hunk in file.hunks for line in hunk.added_lines)


def removed_text(file: ChangedFile) -> str:
    return "\n".join(line.content for hunk in file.hunks for line in hunk.removed_lines)


def context_text(file: ChangedFile) -> str:
    return "\n".join(line.content for hunk in file.hunks for line in hunk.context_lines)


def all_text(file: ChangedFile) -> str:
    return "\n".join([added_text(file), removed_text(file), context_text(file)])


def first_added_line_containing(file: ChangedFile, needles: list[str]) -> DiffLine | None:
    lowered = [needle.lower() for needle in needles]
    for hunk in file.hunks:
        for line in hunk.added_lines:
            content = line.content.lower()
            if any(needle in content for needle in lowered):
                return line
    return None


def first_added_line(file: ChangedFile) -> DiffLine | None:
    for hunk in file.hunks:
        if hunk.added_lines:
            return hunk.added_lines[0]
    return None


def has_test_changes(parsed: ParsedDiff | None, target_stem: str | None = None) -> bool:
    if parsed is None:
        return False

    for file in parsed.files:
        path = file.path.lower()
        if "test" not in path and not path.startswith("tests/"):
            continue
        if target_stem is None or target_stem.lower() in added_text(file).lower():
            return True
    return False
