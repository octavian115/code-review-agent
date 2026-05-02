"""Streamlit frontend for the code review agent."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.routes import initial_state
from backend.api.schemas import ReviewRequest
from backend.graph import build_graph


st.set_page_config(page_title="Code Review Agent", layout="wide")

st.title("Code Review Agent")

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Diff Input")
    uploaded = st.file_uploader("Upload .diff or .patch", type=["diff", "patch"])
    sample_path = ROOT / "evals/test_diffs/auth_bypass_001.diff"
    default_diff = sample_path.read_text() if sample_path.exists() else ""
    raw_diff = st.text_area(
        "Unified diff",
        value=uploaded.read().decode("utf-8") if uploaded else default_diff,
        height=520,
    )
    repo_path = st.text_input("Optional repo path for Ruff/Bandit", value="")
    run = st.button("Run Review", type="primary", use_container_width=True)

with right:
    st.subheader("Review Findings")
    if run:
        request = ReviewRequest(raw_diff=raw_diff, repo_path=repo_path or None)
        with st.spinner("Reviewing diff..."):
            final = build_graph().invoke(initial_state(request))

        tabs = st.tabs(["Findings", "Tool Evidence", "Agent Trace"])
        with tabs[0]:
            st.markdown(final["final_review_markdown"])
        with tabs[1]:
            tool_results = final.get("tool_results", [])
            if tool_results:
                st.dataframe([result.model_dump() for result in tool_results], use_container_width=True)
            else:
                st.info("No static tool findings were produced.")
        with tabs[2]:
            st.json(
                {
                    "bug_findings": [f.model_dump() for f in final.get("bug_findings", [])],
                    "security_findings": [f.model_dump() for f in final.get("security_findings", [])],
                    "test_findings": [f.model_dump() for f in final.get("test_findings", [])],
                    "errors": final.get("errors", []),
                }
            )
    else:
        st.info("Paste a unified diff or upload a patch, then run the review.")
