"""Node: review diff for missing or inadequate test coverage."""

from __future__ import annotations

from backend.models import Finding
from backend.nodes.reviewer_utils import (
    added_text,
    all_text,
    first_added_line,
    has_test_changes,
    removed_text,
)
from backend.state import ReviewState

__test__ = False


def test_reviewer_node(state: ReviewState) -> dict:
    """Review diff for missing or weak tests."""
    parsed = state.get("parsed_diff")
    if parsed is None:
        return {"test_findings": []}

    findings: list[Finding] = []
    test_changed = has_test_changes(parsed)

    for file in parsed.files:
        if file.path.startswith("tests/") or "test" in file.path.lower():
            continue

        added = added_text(file).lower()
        removed = removed_text(file).lower()
        combined = all_text(file).lower()

        security_sensitive = any(
            token in combined
            for token in ("authenticate", "authorization", "password", "token", "permission")
        )
        behavior_changed = bool(added.strip() or removed.strip())

        if security_sensitive and behavior_changed and not test_changed:
            line = first_added_line(file)
            findings.append(
                Finding(
                    source="test_reviewer",
                    title="Security-sensitive behavior changed without tests",
                    description=(
                        "The diff changes authentication or authorization behavior, but "
                        "does not add or update tests to cover the new behavior."
                    ),
                    file_path=file.path,
                    line_number=line.line_number if line else None,
                    severity="medium",
                    confidence=0.74,
                    evidence=["Production auth-related code changed with no test diff."],
                    recommendation=(
                        "Add regression tests for success and failure paths, especially "
                        "invalid credentials and unauthorized access."
                    ),
                )
            )

        if "check_password" in removed and test_changed:
            test_text = "\n".join(
                added_text(test_file).lower()
                for test_file in parsed.files
                if test_file.path.startswith("tests/") or "test" in test_file.path.lower()
            )
            if "invalid" not in test_text and "wrong" not in test_text:
                line = first_added_line(file)
                findings.append(
                    Finding(
                        source="test_reviewer",
                        title="Missing regression test for invalid passwords",
                        description=(
                            "Tests were changed, but the added coverage does not assert "
                            "that a known user with an invalid password is rejected."
                        ),
                        file_path=file.path,
                        line_number=line.line_number if line else None,
                        severity="medium",
                        confidence=0.82,
                        evidence=[
                            "Authentication password checking changed.",
                            "Added tests do not mention invalid or wrong-password behavior.",
                        ],
                        recommendation=(
                            "Add a regression test that calls login/authenticate with an "
                            "existing user and wrong password and expects failure."
                        ),
                    )
                )

    return {"test_findings": findings}
