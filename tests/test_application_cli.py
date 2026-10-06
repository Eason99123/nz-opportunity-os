import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

from application_cli import (
    STATUS_OPTIONS,
    display_applications,
    print_summary,
)


def make_application(
    company="Auckland Council",
    title="Software Engineering Intern",
    status="APPLIED",
):
    return {
        "company": company,
        "title": title,
        "source_link": "https://example.com/job/123",
        "status": status,
        "applied_at": "2026-10-05",
        "last_updated_at": "2026-10-05",
        "notes": "Application submitted.",
    }


def test_status_options_match_tracker_statuses():
    assert set(STATUS_OPTIONS.values()) == {
        "APPLIED",
        "ONLINE_ASSESSMENT",
        "INTERVIEW",
        "OFFER",
        "REJECTED",
        "WITHDRAWN",
    }


def test_display_applications_empty(capsys):
    display_applications([])

    output = capsys.readouterr().out

    assert "No applications recorded." in output


def test_display_applications(capsys):
    applications = [make_application()]

    display_applications(applications)

    output = capsys.readouterr().out

    assert "Auckland Council" in output
    assert "Software Engineering Intern" in output
    assert "APPLIED" in output
    assert "2026-10-05" in output
    assert "https://example.com/job/123" in output
    assert "Application submitted." in output


def test_display_multiple_applications(capsys):
    applications = [
        make_application(),
        make_application(
            company="Serko",
            title="Intern Software Engineer",
            status="INTERVIEW",
        ),
    ]

    display_applications(applications)

    output = capsys.readouterr().out

    assert "1. Auckland Council" in output
    assert "2. Serko" in output
    assert "INTERVIEW" in output


def test_summary_empty(capsys):
    print_summary([])

    output = capsys.readouterr().out

    assert "Total applications: 0" in output


def test_summary_counts_statuses(capsys):
    applications = [
        make_application(),
        make_application(
            company="Serko",
            status="APPLIED",
        ),
        make_application(
            company="Example",
            status="INTERVIEW",
        ),
    ]

    print_summary(applications)

    output = capsys.readouterr().out

    assert "Total applications: 3" in output
    assert "APPLIED: 2" in output
    assert "INTERVIEW: 1" in output