from datetime import date

from src.opportunity_verifier import (
    OPEN_VERIFIED,
    OPEN_UNVERIFIED,
    CLOSED,
    APPLICATION_LINK_BROKEN,
    EXPIRED,
    verify_application_status,
    build_verification_record,
    verify_opportunity,
    is_third_party_url,
    is_official_url,
    is_recognised_ats_url,
)


TODAY = date(2026, 9, 21)


def test_official_application_available_is_verified():
    status = verify_application_status(
        source_url="https://www.linkedin.com/jobs/example",
        employer_apply_url="https://company.wd5.myworkdayjobs.com/job/example",
        application_link_status="OK",
        official_listing_present=True,
        today=TODAY,
    )

    assert status == OPEN_VERIFIED


def test_third_party_only_is_unverified():
    status = verify_application_status(
        source_url="https://nz.prosple.com/example",
        employer_apply_url="",
        application_link_status=None,
        official_listing_present=None,
        today=TODAY,
    )

    assert status == OPEN_UNVERIFIED


def test_broken_application_link_is_broken():
    status = verify_application_status(
        employer_apply_url="https://company.com/jobs/example",
        application_link_status="404",
        official_listing_present=True,
        today=TODAY,
    )

    assert status == APPLICATION_LINK_BROKEN


def test_removed_official_listing_is_closed():
    status = verify_application_status(
        employer_apply_url="https://company.com/jobs/example",
        official_listing_present=False,
        today=TODAY,
    )

    assert status == CLOSED


def test_past_deadline_is_expired():
    status = verify_application_status(
        employer_apply_url="https://company.com/jobs/example",
        deadline="2026-09-20",
        application_link_status="OK",
        official_listing_present=True,
        today=TODAY,
    )

    assert status == EXPIRED


def test_today_deadline_is_not_expired():
    status = verify_application_status(
        employer_apply_url="https://company.com/jobs/example",
        deadline="2026-09-21",
        application_link_status="OK",
        official_listing_present=True,
        today=TODAY,
    )

    assert status == OPEN_VERIFIED


def test_known_job_board_is_third_party():
    assert is_third_party_url(
        "https://www.linkedin.com/jobs/view/123"
    ) is True


def test_employer_domain_is_official():
    assert is_official_url(
        "https://careers.examplecompany.com/jobs/123"
    ) is True


def test_verification_record_contains_required_fields():
    record = build_verification_record(
        employer_apply_url="https://careers.examplecompany.com/jobs/123",
        application_link_status="OK",
        official_listing_present=True,
        today=TODAY,
    )

    assert record["application_status"] == OPEN_VERIFIED
    assert record["employer_apply_url"] == (
        "https://careers.examplecompany.com/jobs/123"
    )
    assert record["last_verified_at"] == "2026-09-21"
    assert record["application_link_status"] == "OK"

def test_existing_opportunity_schema_is_preserved():
    opportunity = {
        "title": "Software Engineering Internship",
        "type": "Internship",
        "where": "Auckland, New Zealand",
        "date_deadline": "Applications close 30 September 2026",
        "why_fit": "Python and automation experience.",
        "next_step": "Apply online.",
        "source_link": "https://www.linkedin.com/jobs/view/123",
        "relevance": 5,
        "beginner_fit": 5,
        "career_value": 5,
        "practicality": 5,
        "university_fit": 5,
        "total_score": 25,
    }

    result = verify_opportunity(
        opportunity,
        today=TODAY,
    )

    assert result["title"] == opportunity["title"]
    assert result["source_link"] == opportunity["source_link"]
    assert result["total_score"] == opportunity["total_score"]
    assert "verification" in result


def test_existing_opportunity_defaults_to_unverified():
    opportunity = {
        "title": "Software Engineering Internship",
        "source_link": "https://www.linkedin.com/jobs/view/123",
    }

    result = verify_opportunity(
        opportunity,
        today=TODAY,
    )

    assert (
        result["verification"]["application_status"]
        == OPEN_UNVERIFIED
    )


def test_existing_opportunity_can_become_verified():
    opportunity = {
        "title": "Test Automation Internship",
        "source_link": "https://www.linkedin.com/jobs/view/123",
    }

    result = verify_opportunity(
        opportunity,
        employer_apply_url=(
            "https://company.wd5.myworkdayjobs.com/job/123"
        ),
        application_link_status="OK",
        official_listing_present=True,
        today=TODAY,
    )

    assert (
        result["verification"]["application_status"]
        == OPEN_VERIFIED
    )

    assert (
        result["verification"]["employer_apply_url"]
        == "https://company.wd5.myworkdayjobs.com/job/123"
    )


def test_verification_does_not_mutate_original_opportunity():
    opportunity = {
        "title": "Software Internship",
        "source_link": "https://nz.prosple.com/example",
    }

    result = verify_opportunity(
        opportunity,
        today=TODAY,
    )

    assert "verification" not in opportunity
    assert "verification" in result

def test_workday_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://microchip.wd5.myworkdayjobs.com/job/123"
    ) is True


def test_workdaysite_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://wd5.myworkdaysite.com/recruiting/company/job/123"
    ) is True


def test_greenhouse_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://boards.greenhouse.io/company/jobs/123"
    ) is True


def test_lever_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://jobs.lever.co/company/123"
    ) is True


def test_smartrecruiters_is_recognised_ats():
    assert is_recognised_ats_url(
        "https://jobs.smartrecruiters.com/company/123"
    ) is True


def test_linkedin_is_not_recognised_ats():
    assert is_recognised_ats_url(
        "https://www.linkedin.com/jobs/view/123"
    ) is False


def test_random_blog_is_not_recognised_ats():
    assert is_recognised_ats_url(
        "https://random-tech-blog.example/jobs/123"
    ) is False


def test_third_party_subdomain_is_detected():
    assert is_third_party_url(
        "https://jobs.linkedin.com/view/123"
    ) is True