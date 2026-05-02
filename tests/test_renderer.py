from backend.models import Finding, ReviewMetadata
from backend.renderer import render_markdown


def test_renderer_no_findings_message():
    markdown = render_markdown([], ReviewMetadata(total_files=1), [])
    assert "No blocking issues found" in markdown


def test_renderer_outputs_finding_location():
    finding = Finding(
        source="security_reviewer",
        title="Password verification bypassed",
        description="A token is created without checking the password.",
        file_path="app/auth.py",
        line_number=10,
        severity="critical",
        confidence=0.96,
        evidence=["Removed check_password"],
        recommendation="Restore password validation.",
    )

    markdown = render_markdown([finding], ReviewMetadata(total_files=1), [])

    assert "CRITICAL" in markdown
    assert "`app/auth.py:10`" in markdown
