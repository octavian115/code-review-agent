from backend.renderer import render_markdown
from backend.state import ReviewState


def render_review_node(state: ReviewState) -> dict:
    markdown = render_markdown(
        findings=state.get("merged_findings", []),
        metadata=state.get("metadata"),
        errors=state.get("errors", []),
    )
    return {"final_review_markdown": markdown}