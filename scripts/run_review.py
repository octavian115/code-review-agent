"""CLI helper for reviewing a pasted .diff/.patch file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.routes import initial_state
from backend.api.schemas import ReviewRequest
from backend.graph import build_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the code review workflow")
    parser.add_argument("diff_file", help="Path to a unified diff or patch file")
    parser.add_argument("--repo-path", default=None, help="Optional repo path for Ruff/Bandit")
    args = parser.parse_args()

    raw_diff = Path(args.diff_file).read_text()
    request = ReviewRequest(raw_diff=raw_diff, repo_path=args.repo_path)
    final = build_graph().invoke(initial_state(request))
    print(final["final_review_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
