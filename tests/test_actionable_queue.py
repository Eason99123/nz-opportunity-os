from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from actionable_queue import (
    build_actionable_queue,
    build_queue_summary,
    get_actionability,
    get_application_status,
    is_actionable,
)


def make_opportunity(status: str) -> dict:
    return {
        "title": f"Test {status}",
        "source_link": "https://example.com/job",
        "total_score": 20,
        "verification": {
            "application_status": status,
        },
    }


def test_get_application_status_open_verified():
    opportunity = make_opportunity("OPEN_VERIFIED")

    assert get_application_status(opportunity) == "OPEN_VERIFIED"


def test_get_application_status_normalises_case_and_spaces():
    opportunity = make_opportunity("  open_verified  ")

    assert get_application_status(opportunity) == "OPEN_VERIFIED"


def test_missing_verification_defaults_to_open_unverified():
    opportunity = {
        "title": "Missing verification",
    }

    assert get_application_status(opportunity) == "OPEN_UNVERIFIED"


def test_missing_application_status_defaults_to_open_unverified():
    opportunity = {
        "title": "Missing status",
        "verification": {},
    }

    assert get_application_status(opportunity) == "OPEN_UNVERIFIED"


def test_invalid_verification_defaults_to_open_unverified():
    opportunity = {
        "title": "Invalid verification",
        "verification": "invalid",
    }

    assert get_application_status(opportunity) == "OPEN_UNVERIFIED"


def test_open_verified_is_actionable():
    opportunity = make_opportunity("OPEN_VERIFIED")

    assert is_actionable(opportunity) is True


def test_open_unverified_is_not_actionable():
    opportunity = make_opportunity("OPEN_UNVERIFIED")

    assert is_actionable(opportunity) is False


def test_closed_is_not_actionable():
    opportunity = make_opportunity("CLOSED")

    assert is_actionable(opportunity) is False


def test_broken_application_link_is_not_actionable():
    opportunity = make_opportunity("APPLICATION_LINK_BROKEN")

    assert is_actionable(opportunity) is False


def test_expired_is_not_actionable():
    opportunity = make_opportunity("EXPIRED")

    assert is_actionable(opportunity) is False


def test_unknown_status_is_not_actionable():
    opportunity = make_opportunity("SOMETHING_NEW")

    result = get_actionability(opportunity)

    assert result["actionable"] is False
    assert result["status"] == "SOMETHING_NEW"
    assert "Unknown verification status" in result["reason"]


def test_open_verified_reason():
    opportunity = make_opportunity("OPEN_VERIFIED")

    result = get_actionability(opportunity)

    assert result == {
        "actionable": True,
        "status": "OPEN_VERIFIED",
        "reason": "Opportunity is verified and open.",
    }


def test_open_unverified_reason():
    opportunity = make_opportunity("OPEN_UNVERIFIED")

    result = get_actionability(opportunity)

    assert result["actionable"] is False
    assert result["status"] == "OPEN_UNVERIFIED"
    assert result["reason"] == (
        "Opportunity has not been verified yet."
    )


def test_build_actionable_queue_only_keeps_verified():
    opportunities = [
        make_opportunity("OPEN_VERIFIED"),
        make_opportunity("OPEN_UNVERIFIED"),
        make_opportunity("CLOSED"),
        make_opportunity("APPLICATION_LINK_BROKEN"),
        make_opportunity("EXPIRED"),
    ]

    queue = build_actionable_queue(opportunities)

    assert len(queue) == 1
    assert (
        queue[0]["verification"]["application_status"]
        == "OPEN_VERIFIED"
    )


def test_build_actionable_queue_empty_input():
    assert build_actionable_queue([]) == []


def test_build_actionable_queue_does_not_mutate_original_list():
    opportunity = make_opportunity("OPEN_VERIFIED")
    opportunities = [opportunity]

    queue = build_actionable_queue(opportunities)

    assert queue is not opportunities
    assert queue[0] is not opportunity
    assert queue[0] == opportunity


def test_queue_summary():
    opportunities = [
        make_opportunity("OPEN_VERIFIED"),
        make_opportunity("OPEN_VERIFIED"),
        make_opportunity("OPEN_UNVERIFIED"),
        make_opportunity("CLOSED"),
        make_opportunity("EXPIRED"),
        make_opportunity("APPLICATION_LINK_BROKEN"),
    ]

    summary = build_queue_summary(opportunities)

    assert summary == {
        "total": 6,
        "actionable": 2,
        "needs_verification": 1,
        "blocked": 3,
    }


def test_queue_summary_missing_verification_needs_verification():
    opportunities = [
        {
            "title": "Unknown opportunity",
        }
    ]

    summary = build_queue_summary(opportunities)

    assert summary == {
        "total": 1,
        "actionable": 0,
        "needs_verification": 1,
        "blocked": 0,
    }


def test_queue_summary_unknown_status_is_blocked():
    opportunities = [
        make_opportunity("UNKNOWN_STATUS"),
    ]

    summary = build_queue_summary(opportunities)

    assert summary == {
        "total": 1,
        "actionable": 0,
        "needs_verification": 0,
        "blocked": 1,
    }