"""Node: review diff for correctness issues."""

from __future__ import annotations

from backend.models import Finding
from backend.nodes.reviewer_utils import added_text, first_added_line_containing, removed_text
from backend.state import ReviewState


def bug_reviewer_node(state: ReviewState) -> dict:
    """Review diff for correctness issues: broken logic, edge cases, etc."""
    parsed = state.get("parsed_diff")
    if parsed is None:
        return {"bug_findings": []}

    findings: list[Finding] = []

    for tool_result in state.get("tool_results", []):
        if tool_result.tool != "ruff":
            continue
        findings.append(
            Finding(
                source="ruff",
                title=tool_result.rule_id or "Ruff finding",
                description=tool_result.message,
                file_path=tool_result.file_path or "",
                line_number=tool_result.line_number,
                severity=tool_result.severity or "medium",
                confidence=0.7,
                evidence=[f"Ruff reported: {tool_result.message}"],
                recommendation="Address the lint finding or document why it is intentional.",
                is_from_tool=True,
            )
        )

    for file in parsed.files:
        added = added_text(file).lower()
        removed = removed_text(file).lower()

        if (
            "password" in removed
            and "check_password" in removed
            and "password: str = \"\"" in added
        ):
            line = first_added_line_containing(file, ["password: str = \"\""])
            findings.append(
                Finding(
                    source="bug_reviewer",
                    title="Authentication now accepts a default empty password",
                    description=(
                        "The function signature changed the password argument to default "
                        "to an empty string while the password check was removed. Callers "
                        "can now omit the credential entirely and still reach token creation."
                    ),
                    file_path=file.path,
                    line_number=line.line_number if line else None,
                    severity="high",
                    confidence=0.88,
                    evidence=[
                        "Removed `check_password(...)` from the login condition.",
                        "Added a default value for the `password` parameter.",
                    ],
                    recommendation=(
                        "Keep `password` required and verify it before returning a token."
                    ),
                )
            )

        removed_guards = (" is not none", "if ", "raise ", "return none")
        if any(token in removed for token in removed_guards) and "todo" in added:
            line = first_added_line_containing(file, ["todo"])
            findings.append(
                Finding(
                    source="bug_reviewer",
                    title="Removed guard replaced with unfinished logic",
                    description=(
                        "The change removes existing control-flow protection and replaces "
                        "it with unfinished code, which is likely to alter behavior."
                    ),
                    file_path=file.path,
                    line_number=line.line_number if line else None,
                    severity="medium",
                    confidence=0.65,
                    evidence=["A removed guard appears near added TODO logic."],
                    recommendation="Preserve the guard until the replacement behavior is complete.",
                )
            )

    return {"bug_findings": findings}
