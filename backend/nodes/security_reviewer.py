"""Node: review diff for security issues."""

from __future__ import annotations

from backend.models import Finding
from backend.nodes.reviewer_utils import added_text, first_added_line_containing, removed_text
from backend.state import ReviewState


def security_reviewer_node(state: ReviewState) -> dict:
    """Review diff for security issues: auth bypasses, injection, etc."""
    parsed = state.get("parsed_diff")
    if parsed is None:
        return {"security_findings": []}

    findings: list[Finding] = []

    for tool_result in state.get("tool_results", []):
        if tool_result.tool != "bandit":
            continue
        findings.append(
            Finding(
                source="bandit",
                title=tool_result.rule_id or "Bandit security finding",
                description=tool_result.message,
                file_path=tool_result.file_path or "",
                line_number=tool_result.line_number,
                severity=tool_result.severity or "medium",
                confidence=0.78,
                evidence=[f"Bandit reported: {tool_result.message}"],
                recommendation="Review the Bandit finding and replace the risky construct if it is reachable.",
                is_from_tool=True,
            )
        )

    for file in parsed.files:
        added = added_text(file).lower()
        removed = removed_text(file).lower()

        password_check_removed = any(
            token in removed
            for token in ("check_password", "verify_password", "password_hash", "bcrypt")
        )
        token_still_created = any(
            token in added
            for token in ("create_token", "jwt", "session", "login_user")
        )
        user_only_condition = (
            "if user:" in added
            or "if user :" in added
            or "password: str = \"\"" in added
            or "password = \"\"" in added
        )

        if password_check_removed and token_still_created and user_only_condition:
            line = first_added_line_containing(
                file, ["if user", "create_token", "password: str = \"\""]
            )
            findings.append(
                Finding(
                    source="security_reviewer",
                    title="Password verification bypassed",
                    description=(
                        "The diff removes password verification while still issuing an "
                        "authentication token for an existing user. That allows login "
                        "without proving knowledge of the password."
                    ),
                    file_path=file.path,
                    line_number=line.line_number if line else None,
                    severity="critical",
                    confidence=0.96,
                    evidence=[
                        "Removed password-checking logic from the authentication path.",
                        "Added logic still returns a token when only the user object exists.",
                    ],
                    recommendation=(
                        "Restore password validation before creating a token, and keep "
                        "failed-password attempts returning an unauthorized response."
                    ),
                )
            )

        dangerous_added = [
            ("subprocess", "shell=True", "Possible shell injection through subprocess shell mode"),
            ("pickle.loads", "", "Unsafe deserialization with pickle.loads"),
            ("yaml.load", "", "Unsafe YAML loading without a safe loader"),
            ("eval(", "", "Dynamic eval on changed input"),
        ]
        for primary, secondary, title in dangerous_added:
            if primary in added and (not secondary or secondary.lower() in added):
                line = first_added_line_containing(file, [primary])
                findings.append(
                    Finding(
                        source="security_reviewer",
                        title=title,
                        description=(
                            "The change introduces a security-sensitive API that can be "
                            "exploitable when fed untrusted input."
                        ),
                        file_path=file.path,
                        line_number=line.line_number if line else None,
                        severity="high",
                        confidence=0.72,
                        evidence=[f"Added code contains `{primary}`."],
                        recommendation="Use a safer API or strictly validate and constrain inputs.",
                    )
                )

    return {"security_findings": findings}
