"""Deterministic renderer: structured findings → markdown review.

This is NOT an LLM call. The final representation is structured.
"""

from __future__ import annotations

from backend.models import Finding, ReviewMetadata


def render_markdown(
    findings: list[Finding],
    metadata: ReviewMetadata | None,
    errors: list[str],
) -> str:
    """Render merged findings into a markdown review report."""

    lines: list[str] = []

    # Header
    lines.append("# Code Review Report")
    lines.append("")

    # Metadata
    if metadata:
        meta_parts = []
        if metadata.total_files:
            meta_parts.append(f"{metadata.total_files} file(s) changed")
        if metadata.total_additions:
            meta_parts.append(f"+{metadata.total_additions}")
        if metadata.total_deletions:
            meta_parts.append(f"-{metadata.total_deletions}")
        if metadata.languages:
            meta_parts.append(f"Languages: {', '.join(metadata.languages)}")
        if meta_parts:
            lines.append(f"**Scope:** {' | '.join(meta_parts)}")
            lines.append("")

    # Static analysis note
    if metadata and not metadata.has_repo_path:
        lines.append(
            "> *Static analysis was not available — findings are based on "
            "LLM analysis only.*"
        )
        lines.append("")
    elif metadata and metadata.tools_failed:
        failed = ", ".join(metadata.tools_failed)
        lines.append(
            f"> *Some static analysis tools failed ({failed}) — related "
            f"findings are based on LLM analysis only.*"
        )
        lines.append("")

    # Findings
    if not findings:
        lines.append("**No blocking issues found.** This change looks good to merge.")
    else:
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            findings, key=lambda f: severity_order.get(f.severity, 4)
        )

        count = len(sorted_findings)
        lines.append(
            f"Found **{count} issue{'s' if count != 1 else ''}** worth addressing.\n"
        )

        for i, finding in enumerate(sorted_findings, 1):
            sev = finding.severity.upper()
            lines.append(f"### {i}. {sev}: {finding.title}")
            lines.append("")

            loc = f"`{finding.file_path}"
            if finding.line_number:
                loc += f":{finding.line_number}"
            loc += "`"
            lines.append(
                f"**File:** {loc} | **Confidence:** {finding.confidence:.2f} "
                f"| **Source:** {finding.source}"
            )
            lines.append("")
            lines.append(finding.description)
            lines.append("")

            if finding.evidence:
                lines.append("**Evidence:**")
                for ev in finding.evidence:
                    lines.append(f"- {ev}")
                lines.append("")

            lines.append(f"**Recommendation:** {finding.recommendation}")
            lines.append("")

    # Errors / limitations
    if errors:
        lines.append("---")
        lines.append("### Limitations")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    return "\n".join(lines)
