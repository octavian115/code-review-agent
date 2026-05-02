"""Scoring utilities for seeded diff evals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.models import Finding


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass
class CaseScore:
    case_id: str
    passed: bool
    detected_expected: bool
    false_positive: bool
    duplicate_count: int
    severity_match: bool


def _matches_expected(finding: Finding, expected: dict[str, Any]) -> bool:
    if finding.file_path != expected["file_path"]:
        return False
    start, end = expected["line_range"]
    line = finding.line_number
    return line is None or start - 2 <= line <= end + 2


def score_case(case: dict[str, Any], findings: list[Finding]) -> CaseScore:
    expected = case.get("expected_findings", [])
    should_have = bool(case.get("should_have_findings"))

    detected_expected = True
    severity_match = True

    for item in expected:
        matches = [finding for finding in findings if _matches_expected(finding, item)]
        if not matches:
            detected_expected = False
            severity_match = False
            continue
        expected_rank = SEVERITY_RANK[item["severity"]]
        severity_match = severity_match and any(
            SEVERITY_RANK[finding.severity] >= expected_rank for finding in matches
        )

    false_positive = not should_have and bool(findings)
    duplicate_count = max(0, len(findings) - len({(f.file_path, f.line_number, f.title) for f in findings}))
    passed = detected_expected and severity_match and not false_positive

    return CaseScore(
        case_id=case["id"],
        passed=passed,
        detected_expected=detected_expected,
        false_positive=false_positive,
        duplicate_count=duplicate_count,
        severity_match=severity_match,
    )
