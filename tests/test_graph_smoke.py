"""
Smoke test: validate diff parser, models, and graph skeleton.

Run: python -m tests.test_graph_smoke
"""

from pathlib import Path

from backend.diff_parser import parse_diff
from backend.models import Finding
from backend.state import ReviewState


def test_parser():
    """Test that the diff parser correctly handles the auth bypass diff."""
    diff_path = Path("evals/test_diffs/auth_bypass_001.diff")
    raw_diff = diff_path.read_text()

    parsed = parse_diff(raw_diff)

    print("=== DIFF PARSER TEST ===\n")
    print(f"Total files changed: {parsed.total_files}")
    print(f"Total additions: {parsed.total_additions}")
    print(f"Total deletions: {parsed.total_deletions}")
    print()

    for f in parsed.files:
        print(f"  File: {f.path} ({f.status}) [{f.language}]")
        for hunk in f.hunks:
            print(f"    Hunk: @@ -{hunk.old_start},{hunk.old_lines} +{hunk.new_start},{hunk.new_lines} @@")
            for line in hunk.removed_lines:
                print(f"      - L{line.line_number}: {line.content}")
            for line in hunk.added_lines:
                print(f"      + L{line.line_number}: {line.content}")
        print()

    assert parsed.total_files == 3, f"Expected 3 files, got {parsed.total_files}"
    assert parsed.files[0].path == "app/auth.py"
    assert parsed.files[0].status == "modified"
    assert parsed.files[0].language == "python"
    assert parsed.files[1].path == "app/routes.py"
    assert parsed.files[2].path == "tests/test_auth.py"
    assert parsed.total_additions > 0
    assert parsed.total_deletions > 0

    changed = parsed.changed_line_numbers
    assert "app/auth.py" in changed
    assert len(changed["app/auth.py"]) > 0

    print("✓ All parser assertions passed.\n")


def test_finding_model():
    """Test that the Finding model validates correctly."""
    print("=== FINDING MODEL TEST ===\n")

    finding = Finding(
        source="security_reviewer",
        title="Password verification bypassed",
        description="The updated condition authenticates any existing user.",
        file_path="app/auth.py",
        line_number=10,
        severity="critical",
        confidence=0.96,
        evidence=["Removed check_password call", "New condition only checks user exists"],
        recommendation="Restore password validation before issuing a token.",
    )

    assert finding.severity == "critical"
    assert finding.confidence == 0.96
    assert len(finding.evidence) == 2
    print(f"  Finding: {finding.title} ({finding.severity}, {finding.confidence})")
    print("✓ Finding model test passed.\n")


def test_graph_skeleton():
    """Test that the graph compiles and runs end-to-end with stub nodes."""
    from backend.graph import build_graph

    diff_path = Path("evals/test_diffs/auth_bypass_001.diff")
    raw_diff = diff_path.read_text()

    graph = build_graph()

    print("=== GRAPH SKELETON TEST ===\n")
    print(f"Graph nodes: {list(graph.get_graph().nodes.keys())}")
    print()

    initial_state: ReviewState = {
        "raw_diff": raw_diff,
        "repo_path": None,
        "parsed_diff": None,
        "metadata": None,
        "tool_results": [],
        "bug_findings": [],
        "security_findings": [],
        "test_findings": [],
        "filtered_findings": [],
        "merged_findings": [],
        "final_review_markdown": "",
        "errors": [],
    }

    # Stream to see node-by-node execution
    for event in graph.stream(initial_state, stream_mode="updates"):
        for node_name, update in event.items():
            print(f"  Node: {node_name}")
            if node_name == "parse_diff" and update.get("parsed_diff"):
                pd = update["parsed_diff"]
                print(f"    → Parsed {pd.total_files} files, +{pd.total_additions}/-{pd.total_deletions}")
            if node_name == "render_review":
                print(f"    → Review length: {len(update.get('final_review_markdown', ''))} chars")

    # Verify final state
    final = graph.invoke(initial_state)
    assert final["parsed_diff"] is not None
    assert final["metadata"] is not None
    assert final["final_review_markdown"] != ""
    assert "Password verification bypassed" in final["final_review_markdown"]
    assert final["merged_findings"]

    print()
    print("=== FINAL REVIEW ===\n")
    print(final["final_review_markdown"])
    print("✓ Graph skeleton test passed.\n")


if __name__ == "__main__":
    test_parser()
    test_finding_model()
    test_graph_skeleton()
    print("=" * 50)
    print("All smoke tests passed!")
