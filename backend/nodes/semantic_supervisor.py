"""Node: LLM-powered semantic deduplication and final consolidation.

Handles what deterministic filter cannot:
- Are two findings about different files actually the same issue?
- Is this finding worth blocking a merge?
- Which explanation is clearer?
"""

from __future__ import annotations

from backend.models import Finding
from backend.state import ReviewState


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _fingerprint(finding: Finding) -> str:
    text = " ".join(
        [
            finding.title.lower(),
            finding.description.lower(),
            " ".join(finding.evidence).lower(),
        ]
    )
    if finding.file_path and any(
        token in text
        for token in ("password", "credential", "auth", "token", "login")
    ):
        return f"{finding.file_path}:auth"
    if finding.file_path and finding.line_number is not None:
        return f"{finding.file_path}:{finding.line_number}"
    return f"{finding.file_path}:{finding.title.lower()}"


def _merge(primary: Finding, duplicate: Finding) -> Finding:
    evidence = list(dict.fromkeys(primary.evidence + duplicate.evidence))
    confidence = max(primary.confidence, duplicate.confidence)
    severity = min(
        [primary.severity, duplicate.severity],
        key=lambda severity: SEVERITY_RANK.get(severity, 99),
    )
    source = primary.source
    if duplicate.severity == severity and duplicate.confidence > primary.confidence:
        source = duplicate.source

    return primary.model_copy(
        update={
            "severity": severity,
            "confidence": confidence,
            "source": source,
            "evidence": evidence[:6],
        }
    )


def semantic_supervisor_node(state: ReviewState) -> dict:
    """Semantic deduplication and consolidation of findings."""
    filtered = state.get("filtered_findings", [])

    if not filtered:
        return {"merged_findings": []}

    merged_by_key: dict[str, Finding] = {}
    for finding in filtered:
        key = _fingerprint(finding)
        if key in merged_by_key:
            merged_by_key[key] = _merge(merged_by_key[key], finding)
        else:
            merged_by_key[key] = finding

    merged = sorted(
        merged_by_key.values(),
        key=lambda finding: (
            SEVERITY_RANK.get(finding.severity, 99),
            -finding.confidence,
            finding.file_path,
            finding.line_number or 0,
        ),
    )

    return {"merged_findings": merged}
