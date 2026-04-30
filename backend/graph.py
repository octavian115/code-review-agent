"""
LangGraph workflow for the code review agent.

This file is intentionally thin: it imports node functions and wires them.
All logic lives in backend/nodes/ and backend/renderer.py.

Architecture:
    parse_diff → run_static_tools → [bug, security, test reviewers]
    → deterministic_filter → semantic_supervisor → render_review
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.nodes.bug_reviewer import bug_reviewer_node
from backend.nodes.deterministic_filter import deterministic_filter_node
from backend.nodes.parse_diff import parse_diff_node
from backend.nodes.security_reviewer import security_reviewer_node
from backend.nodes.semantic_supervisor import semantic_supervisor_node
from backend.nodes.static_tools import run_static_tools_node
from backend.nodes.test_reviewer import test_reviewer_node
from backend.nodes.render_review import render_review_node
from backend.state import ReviewState


def build_graph():
    """Build the code review agent graph.

    Flow:
        START → parse_diff → run_static_tools
              → [bug_reviewer, security_reviewer, test_reviewer] (parallel)
              → deterministic_filter → semantic_supervisor
              → render_review → END
    """
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("parse_diff", parse_diff_node)
    workflow.add_node("run_static_tools", run_static_tools_node)
    workflow.add_node("bug_reviewer", bug_reviewer_node)
    workflow.add_node("security_reviewer", security_reviewer_node)
    workflow.add_node("test_reviewer", test_reviewer_node)
    workflow.add_node("deterministic_filter", deterministic_filter_node)
    workflow.add_node("semantic_supervisor", semantic_supervisor_node)
    workflow.add_node("render_review", render_review_node)

    # Sequential start
    workflow.add_edge(START, "parse_diff")
    workflow.add_edge("parse_diff", "run_static_tools")

    # Fan out to parallel reviewers
    workflow.add_edge("run_static_tools", "bug_reviewer")
    workflow.add_edge("run_static_tools", "security_reviewer")
    workflow.add_edge("run_static_tools", "test_reviewer")

    # Converge into two-stage supervisor
    workflow.add_edge("bug_reviewer", "deterministic_filter")
    workflow.add_edge("security_reviewer", "deterministic_filter")
    workflow.add_edge("test_reviewer", "deterministic_filter")

    workflow.add_edge("deterministic_filter", "semantic_supervisor")
    workflow.add_edge("semantic_supervisor", "render_review")
    workflow.add_edge("render_review", END)

    return workflow.compile()
