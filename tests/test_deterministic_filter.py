from backend.models import ChangedFile, DiffLine, Finding, Hunk, ParsedDiff
from backend.nodes.deterministic_filter import deterministic_filter_node


def _finding(confidence: float, line: int = 10) -> Finding:
    return Finding(
        source="bug_reviewer",
        title="Bug",
        description="Something changed badly",
        file_path="app/example.py",
        line_number=line,
        severity="high",
        confidence=confidence,
        evidence=["evidence"],
        recommendation="Fix it",
    )


def test_filter_drops_low_confidence_and_keeps_near_changed_lines():
    parsed = ParsedDiff(
        files=[
            ChangedFile(
                path="app/example.py",
                status="modified",
                hunks=[
                    Hunk(
                        old_start=10,
                        old_lines=1,
                        new_start=10,
                        new_lines=1,
                        added_lines=[DiffLine(line_number=10, content="new")],
                    )
                ],
            )
        ]
    )
    state = {
        "parsed_diff": parsed,
        "bug_findings": [_finding(0.5), _finding(0.8, line=12), _finding(0.9, line=30)],
        "security_findings": [],
        "test_findings": [],
    }

    result = deterministic_filter_node(state)

    assert len(result["filtered_findings"]) == 1
    assert result["filtered_findings"][0].line_number == 12
