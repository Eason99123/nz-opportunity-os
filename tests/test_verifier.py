from datetime import date
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from opportunity_verifier import (
    OPEN_VERIFIED,
    OPEN_UNVERIFIED,
    CLOSED,
    APPLICATION_LINK_BROKEN,
    EXPIRED,
    is_third_party_url,
    is_recognised_ats_url,
    is_official_url,
    verify_application_status,
    build_verification_record,
    verify_opportunity,
    verify_opportunities,
)


TEST_TODAY = date(2026, 9, 22)


# ============================================================
# URL classification
# ============================================================

def test_linkedin_is_third_party():
    assert is_third_party_url(
        "https://www.linkedin.com/jobs/view/123"
    ) is True


def test_seek_is_third_party():
    assert is_third_party_url(
        "https://www.seek.co.nz/job/123"
    ) is True


def test_employer_site_is_not_third_party():
    assert is_third_party_url(
        "https://careers.examplecompany.com/job/123"
    ) is False


def test_workday_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://company.wd5.myworkdaysite.com/job/123"
    ) is True


def test_greenhouse_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://boards.greenhouse.io/company/jobs/123"
    ) is True


def test_linkedin_is_not_official():
    assert is_official_url(
        "https://www.linkedin.com/jobs/view/123"
    ) is False


def test_employer_site_is_official():
    assert is_official_url(
        "https://careers.examplecompany.com/job/123"
    ) is True


# ============================================================
# OPEN_UNVERIFIED
# ============================================================

def test_unknown_opportunity_is_open_unverified():
    status = verify_application_status(
        source_url="https://www.linkedin.com/jobs/view/123",
        today=TEST_TODAY,
    )

    assert status == OPEN_UNVERIFIED


def test_official_url_without_confirmation_is_unverified():
    status = verify_application_status(
        source_url="https://careers.examplecompany.com/job/123",
        employer_apply_url="https://careers.examplecompany.com/job/123",
        today=TEST_TODAY,
    )

    assert status == OPEN_UNVERIFIED


# ============================================================
# OPEN_VERIFIED
# ============================================================

def test_confirmed_official_application_is_open_verified():
    status = verify_application_status(
        employer_apply_url=(
            "https://careers.examplecompany.com/job/123"
        ),
        application_link_status="OK",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == OPEN_VERIFIED


def test_confirmed_workday_application_is_open_verified():
    status = verify_application_status(
        employer_apply_url=(
            "https://company.wd5.myworkdaysite.com/job/123"
        ),
        application_link_status="OK",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == OPEN_VERIFIED


def test_third_party_application_cannot_be_open_verified():
    status = verify_application_status(
        employer_apply_url=(
            "https://www.linkedin.com/jobs/view/123"
        ),
        application_link_status="OK",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == OPEN_UNVERIFIED


# ============================================================
# CLOSED
# ============================================================

def test_removed_official_listing_is_closed():
    status = verify_application_status(
        employer_apply_url=(
            "https://careers.examplecompany.com/job/123"
        ),
        application_link_status="OK",
        official_listing_present=False,
        today=TEST_TODAY,
    )

    assert status == CLOSED


# ============================================================
# APPLICATION_LINK_BROKEN
# ============================================================

def test_broken_application_link():
    status = verify_application_status(
        employer_apply_url=(
            "https://careers.examplecompany.com/job/123"
        ),
        application_link_status="BROKEN",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == APPLICATION_LINK_BROKEN


def test_404_application_link():
    status = verify_application_status(
        employer_apply_url=(
            "https://careers.examplecompany.com/job/123"
        ),
        application_link_status="404",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == APPLICATION_LINK_BROKEN


def test_error_application_link():
    status = verify_application_status(
        employer_apply_url=(
            "https://careers.examplecompany.com/job/123"
        ),
        application_link_status="ERROR",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == APPLICATION_LINK_BROKEN


# ============================================================
# EXPIRED
# ============================================================

def test_past_iso_deadline_is_expired():
    status = verify_application_status(
        deadline="2026-09-21",
        today=TEST_TODAY,
    )

    assert status == EXPIRED


def test_past_slash_deadline_is_expired():
    status = verify_application_status(
        deadline="21/09/2026",
        today=TEST_TODAY,
    )

    assert status == EXPIRED


def test_past_dash_deadline_is_expired():
    status = verify_application_status(
        deadline="21-09-2026",
        today=TEST_TODAY,
    )

    assert status == EXPIRED


def test_deadline_today_is_not_expired():
    status = verify_application_status(
        deadline="2026-09-22",
        today=TEST_TODAY,
    )

    assert status == OPEN_UNVERIFIED


def test_future_deadline_is_not_expired():
    status = verify_application_status(
        deadline="2026-10-01",
        today=TEST_TODAY,
    )

    assert status == OPEN_UNVERIFIED


# ============================================================
# Rule priority
# ============================================================

def test_expired_has_priority_over_broken_link():
    status = verify_application_status(
        deadline="2026-09-20",
        application_link_status="BROKEN",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert status == EXPIRED


def test_broken_link_has_priority_over_closed():
    status = verify_application_status(
        application_link_status="BROKEN",
        official_listing_present=False,
        today=TEST_TODAY,
    )

    assert status == APPLICATION_LINK_BROKEN


# ============================================================
# Verification record
# ============================================================

def test_build_verification_record_open_verified():
    record = build_verification_record(
        employer_apply_url=(
            "https://company.wd5.myworkdaysite.com/job/123"
        ),
        application_link_status="OK",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert record["application_status"] == OPEN_VERIFIED
    assert record["application_link_status"] == "OK"
    assert record["last_verified_at"] == "2026-09-22"


# ============================================================
# Opportunity integration
# ============================================================

def test_verify_opportunity_preserves_original_fields():
    opportunity = {
        "title": "Software Engineering Intern",
        "source_link": "https://www.linkedin.com/jobs/view/123",
        "total_score": 25,
    }

    verified = verify_opportunity(
        opportunity,
        today=TEST_TODAY,
    )

    assert verified["title"] == "Software Engineering Intern"
    assert verified["total_score"] == 25
    assert verified["verification"]["application_status"] == (
        OPEN_UNVERIFIED
    )


def test_verify_opportunity_does_not_modify_original():
    opportunity = {
        "title": "Software Engineering Intern",
        "source_link": "https://www.linkedin.com/jobs/view/123",
    }

    verify_opportunity(
        opportunity,
        today=TEST_TODAY,
    )

    assert "verification" not in opportunity


def test_verify_opportunity_can_be_open_verified():
    opportunity = {
        "title": "Test Automation Intern",
        "source_link": "https://example.com/job",
    }

    verified = verify_opportunity(
        opportunity,
        employer_apply_url=(
            "https://company.wd5.myworkdaysite.com/job/123"
        ),
        application_link_status="OK",
        official_listing_present=True,
        today=TEST_TODAY,
    )

    assert verified["verification"]["application_status"] == (
        OPEN_VERIFIED
    )

    assert verified["verification"]["official_listing_present"] is True


# ============================================================
# Collection integration
# ============================================================

def test_verify_opportunities_returns_all_items():
    opportunities = [
        {
            "title": "Opportunity A",
            "source_link": "https://example.com/a",
        },
        {
            "title": "Opportunity B",
            "source_link": "https://example.com/b",
        },
    ]

    verified = verify_opportunities(opportunities)

    assert len(verified) == 2

    assert all(
        "verification" in opportunity
        for opportunity in verified
    )


def test_verify_opportunities_defaults_to_unverified():
    opportunities = [
        {
            "title": "Opportunity A",
            "source_link": "https://example.com/a",
        },
        {
            "title": "Opportunity B",
            "source_link": "https://example.com/b",
        },
    ]

    verified = verify_opportunities(opportunities)

    assert all(
        opportunity["verification"]["application_status"]
        == OPEN_UNVERIFIED
        for opportunity in verified
    )