from copy import deepcopy
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

from actionable_queue import is_actionable
from verification_updater import (
    apply_verification_result,
    apply_verification_results,
)


def make_unverified_opportunity():
    return {
        "title": "Software Engineering Internship",
        "source_link": "https://example.com/job/123",
        "total_score": 24,
        "verification": {
            "application_status": "OPEN_UNVERIFIED",
            "employer_apply_url": "",
            "last_verified_at": "2026-10-01",
            "application_link_status": "",
            "official_listing_present": None,
        },
    }


def test_apply_verification_result_upgrades_to_open_verified():
    opportunity = make_unverified_opportunity()

    updated = apply_verification_result(
        opportunity,
        application_status="OPEN_VERIFIED",
        employer_apply_url="https://example.com/apply/123",
        application_link_status="WORKING",
        official_listing_present=True,
        verification_reason="Official listing confirmed.",
        last_verified_at="2026-10-04",
    )

    verification = updated["verification"]

    assert verification["application_status"] == "OPEN_VERIFIED"
    assert (
        verification["employer_apply_url"]
        == "https://example.com/apply/123"
    )
    assert verification["application_link_status"] == "WORKING"
    assert verification["official_listing_present"] is True
    assert (
        verification["verification_reason"]
        == "Official listing confirmed."
    )
    assert verification["last_verified_at"] == "2026-10-04"


def test_apply_verification_result_does_not_mutate_original():
    opportunity = make_unverified_opportunity()
    original = deepcopy(opportunity)

    apply_verification_result(
        opportunity,
        application_status="OPEN_VERIFIED",
        official_listing_present=True,
    )

    assert opportunity == original


def test_verified_opportunity_becomes_actionable():
    opportunity = make_unverified_opportunity()

    assert is_actionable(opportunity) is False

    updated = apply_verification_result(
        opportunity,
        application_status="OPEN_VERIFIED",
        employer_apply_url="https://example.com/apply/123",
        application_link_status="WORKING",
        official_listing_present=True,
    )

    assert is_actionable(updated) is True


def test_closed_result_remains_not_actionable():
    opportunity = make_unverified_opportunity()

    updated = apply_verification_result(
        opportunity,
        application_status="CLOSED",
        official_listing_present=False,
        verification_reason="Official listing has closed.",
    )

    assert is_actionable(updated) is False


def test_invalid_status_raises_value_error():
    opportunity = make_unverified_opportunity()

    with pytest.raises(ValueError):
        apply_verification_result(
            opportunity,
            application_status="UNKNOWN_STATUS",
        )


def test_apply_multiple_verification_results():
    first = make_unverified_opportunity()

    second = {
        "title": "AI Internship",
        "source_link": "https://example.com/job/456",
        "total_score": 22,
        "verification": {
            "application_status": "OPEN_UNVERIFIED",
        },
    }

    opportunities = [first, second]

    results = {
        "https://example.com/job/123": {
            "application_status": "OPEN_VERIFIED",
            "official_listing_present": True,
            "application_link_status": "WORKING",
            "last_verified_at": "2026-10-04",
        }
    }

    updated = apply_verification_results(
        opportunities,
        results,
    )

    assert (
        updated[0]["verification"]["application_status"]
        == "OPEN_VERIFIED"
    )

    assert (
        updated[1]["verification"]["application_status"]
        == "OPEN_UNVERIFIED"
    )


def test_batch_update_does_not_mutate_input():
    opportunity = make_unverified_opportunity()
    opportunities = [opportunity]
    original = deepcopy(opportunities)

    results = {
        "https://example.com/job/123": {
            "application_status": "OPEN_VERIFIED",
        }
    }

    apply_verification_results(
        opportunities,
        results,
    )

    assert opportunities == original