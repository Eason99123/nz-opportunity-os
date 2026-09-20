from datetime import date, datetime
from urllib.parse import urlparse


# ============================================================
# Application verification statuses
# ============================================================

OPEN_VERIFIED = "OPEN_VERIFIED"
OPEN_UNVERIFIED = "OPEN_UNVERIFIED"
CLOSED = "CLOSED"
APPLICATION_LINK_BROKEN = "APPLICATION_LINK_BROKEN"
EXPIRED = "EXPIRED"


# ============================================================
# Known third-party job platforms
#
# These websites can help us discover opportunities, but their
# presence alone is not enough to mark an opportunity as
# OPEN_VERIFIED.
# ============================================================

THIRD_PARTY_DOMAINS = {
    "linkedin.com",
    "indeed.com",
    "nz.indeed.com",
    "prosple.com",
    "nz.prosple.com",
    "seek.co.nz",
}


# ============================================================
# Recognised Applicant Tracking Systems (ATS)
#
# These platforms are commonly used by employers as official
# recruitment/application systems.
# ============================================================

RECOGNISED_ATS_DOMAINS = {
    "myworkdayjobs.com",
    "myworkdaysite.com",
    "greenhouse.io",
    "boards.greenhouse.io",
    "lever.co",
    "jobs.lever.co",
    "smartrecruiters.com",
    "jobs.smartrecruiters.com",
    "ashbyhq.com",
    "jobs.ashbyhq.com",
    "successfactors.com",
}


# ============================================================
# URL helpers
# ============================================================

def _domain(url):
    """
    Return the lowercase domain for a URL.

    Example:
        https://www.linkedin.com/jobs/123
        -> www.linkedin.com
    """

    if not url:
        return ""

    try:
        return urlparse(url).netloc.lower()
    except (TypeError, ValueError):
        return ""


def _domain_matches(domain, known_domain):
    """
    Match an exact domain or one of its subdomains.

    Example:
        jobs.linkedin.com matches linkedin.com
        abc.jobs.lever.co matches lever.co
    """

    return (
        domain == known_domain
        or domain.endswith("." + known_domain)
    )


# ============================================================
# Source classification
# ============================================================

def is_third_party_url(url):
    """
    Return True when the URL belongs to a known third-party
    job platform.

    Third-party sources are useful for discovery, but cannot
    independently prove that an opportunity is still open.
    """

    domain = _domain(url)

    if not domain:
        return False

    return any(
        _domain_matches(domain, known_domain)
        for known_domain in THIRD_PARTY_DOMAINS
    )


def is_recognised_ats_url(url):
    """
    Return True when the URL belongs to a recognised
    Applicant Tracking System.
    """

    domain = _domain(url)

    if not domain:
        return False

    return any(
        _domain_matches(domain, known_domain)
        for known_domain in RECOGNISED_ATS_DOMAINS
    )


def is_official_url(url):
    """
    Return True when a URL is not a known third-party source.

    Important:
    This is currently a broad classification.

    A non-third-party URL is not automatically proof that the
    URL belongs to the employer. Employer identity verification
    will be handled by the Source Trust Model in a later stage.
    """

    domain = _domain(url)

    if not domain:
        return False

    return not is_third_party_url(url)


# ============================================================
# Deadline handling
# ============================================================

def _parse_deadline(deadline):
    """
    Parse a deadline into a date object when possible.

    Supported examples:
        2026-09-30
        30/09/2026
        30-09-2026

    Natural-language deadline fields from the existing OS are
    intentionally not parsed here yet.
    """

    if not deadline:
        return None

    if isinstance(deadline, datetime):
        return deadline.date()

    if isinstance(deadline, date):
        return deadline

    if isinstance(deadline, str):
        value = deadline.strip()

        for fmt in (
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(
                    value,
                    fmt,
                ).date()
            except ValueError:
                continue

    return None


# ============================================================
# Application status verification
# ============================================================

def verify_application_status(
    source_url="",
    employer_apply_url="",
    deadline=None,
    application_link_status=None,
    official_listing_present=None,
    today=None,
):
    """
    Determine the current application status of an opportunity.

    Possible results:
        OPEN_VERIFIED
        OPEN_UNVERIFIED
        CLOSED
        APPLICATION_LINK_BROKEN
        EXPIRED

    Parameters
    ----------
    source_url:
        Original discovery URL.

        Example:
            LinkedIn
            Prosple
            Indeed
            employer page

    employer_apply_url:
        Employer or ATS application URL.

    deadline:
        Normalised deadline when available.

    application_link_status:
        Examples:
            OK
            BROKEN
            404
            ERROR

    official_listing_present:
        True
            Official listing confirmed present.

        False
            Official listing confirmed removed.

        None
            Not checked or unknown.

    today:
        Allows deterministic testing.
    """

    if today is None:
        today = date.today()

    # --------------------------------------------------------
    # Rule 1: expired deadline
    # --------------------------------------------------------

    parsed_deadline = _parse_deadline(deadline)

    if (
        parsed_deadline is not None
        and parsed_deadline < today
    ):
        return EXPIRED

    # --------------------------------------------------------
    # Rule 2: broken application link
    # --------------------------------------------------------

    if application_link_status:
        link_status = str(
            application_link_status
        ).strip().upper()

        if link_status in {
            "BROKEN",
            "404",
            "ERROR",
        }:
            return APPLICATION_LINK_BROKEN

    # --------------------------------------------------------
    # Rule 3: official listing confirmed removed
    # --------------------------------------------------------

    if official_listing_present is False:
        return CLOSED

    # --------------------------------------------------------
    # Rule 4: official listing + working application URL
    # --------------------------------------------------------

    if (
        official_listing_present is True
        and is_official_url(employer_apply_url)
        and str(
            application_link_status
        ).strip().upper() == "OK"
    ):
        return OPEN_VERIFIED

    # --------------------------------------------------------
    # Rule 5: insufficient evidence
    # --------------------------------------------------------

    return OPEN_UNVERIFIED


# ============================================================
# Verification record
# ============================================================

def build_verification_record(
    source_url="",
    employer_apply_url="",
    deadline=None,
    application_link_status=None,
    official_listing_present=None,
    today=None,
):
    """
    Create the verification metadata stored with an opportunity.
    """

    if today is None:
        today = date.today()

    status = verify_application_status(
        source_url=source_url,
        employer_apply_url=employer_apply_url,
        deadline=deadline,
        application_link_status=application_link_status,
        official_listing_present=official_listing_present,
        today=today,
    )

    return {
        "application_status": status,
        "employer_apply_url": (
            employer_apply_url or ""
        ),
        "last_verified_at": today.isoformat(),
        "application_link_status": (
            application_link_status or ""
        ),
    }


# ============================================================
# Existing Opportunity OS schema integration
# ============================================================

def verify_opportunity(
    opportunity,
    employer_apply_url="",
    application_link_status=None,
    official_listing_present=None,
    today=None,
):
    """
    Add verification metadata to an existing opportunity
    without changing or removing the original fields.

    Existing Opportunity OS example:

        {
            "title": "...",
            "type": "...",
            "where": "...",
            "date_deadline": "...",
            "why_fit": "...",
            "next_step": "...",
            "source_link": "...",
            "relevance": 5,
            "beginner_fit": 5,
            "career_value": 5,
            "practicality": 5,
            "university_fit": 5,
            "total_score": 25
        }

    The result receives an additional:

        "verification": {...}

    field.

    The original dictionary is not modified.
    """

    if today is None:
        today = date.today()

    source_url = opportunity.get(
        "source_link",
        "",
    )

    # date_deadline is intentionally not passed here yet.
    #
    # The existing OS stores deadline information as natural
    # language such as:
    #
    # "22 September 2026; registration currently available"
    #
    # Deadline normalisation will be implemented separately.

    record = build_verification_record(
        source_url=source_url,
        employer_apply_url=employer_apply_url,
        application_link_status=application_link_status,
        official_listing_present=official_listing_present,
        today=today,
    )

    verified = opportunity.copy()

    verified["verification"] = {
        **record,
        "official_listing_present": (
            official_listing_present
        ),
    }

    return verified

def verify_opportunities(
    opportunities: list[dict],
) -> list[dict]:
    """
    Verify a collection of opportunities.

    Each opportunity is passed through verify_opportunity().
    A new list is returned so the caller can safely continue
    with ranking and exporting.
    """
    return [
        verify_opportunity(opportunity)
        for opportunity in opportunities
    ]