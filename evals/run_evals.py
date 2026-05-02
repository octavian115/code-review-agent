"""Run seeded code-review evals.

Usage:
    python -m evals.run_evals
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.api.routes import initial_state
from backend.api.schemas import ReviewRequest
from backend.graph import build_graph
from evals.scorers import score_case


ROOT = Path(__file__).resolve().parents[1]


def _load_diff(case: dict) -> str:
    if "diff" in case:
        return case["diff"]
    return (ROOT / case["diff_path"]).read_text()


def run() -> int:
    dataset = json.loads((ROOT / "evals/golden_dataset.json").read_text())
    graph = build_graph()
    scores = []

    for case in dataset:
        request = ReviewRequest(raw_diff=_load_diff(case), repo_path=None)
        final = graph.invoke(initial_state(request))
        scores.append(score_case(case, final.get("merged_findings", [])))

    passed = sum(1 for score in scores if score.passed)
    total = len(scores)

    print(f"Eval cases: {passed}/{total} passed")
    for score in scores:
        status = "PASS" if score.passed else "FAIL"
        print(
            f"- {status} {score.case_id}: detected={score.detected_expected} "
            f"severity={score.severity_match} false_positive={score.false_positive} "
            f"duplicates={score.duplicate_count}"
        )

    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())
