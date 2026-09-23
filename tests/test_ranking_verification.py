import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ranking import (
    generate_verification_actions,
    get_best_actionable_opportunity,
    get_top_unverified_opportunity,
    get_verification_status,
)


def make_opportunity(
    title,
    score,
    status,
):
    return {
        "title": title,
        "total_score": score,
        "source_link": f"https://example.com/{title}",
        "verification": {
            "application_status": status,
        },
    }


def test_get_verification_status_verified():
    opportunity = make_opportunity(
        "Verified Job",
        20,
        "OPEN_VERIFIED",
    )

    assert (
        get_verification_status(opportunity)
        == "OPEN_VERIFIED"
    )


def test_missing_verification_defaults_to_unverified():
    opportunity = {
        "title": "Unknown Job",
        "total_score": 20,
    }

    assert (
        get_verification_status(opportunity)
        == "OPEN_UNVERIFIED"
    )


def test_empty_status_defaults_to_unverified():
    opportunity = {
        "title": "Unknown Job",
        "verification": {
            "application_status": "",
        },
    }

    assert (
        get_verification_status(opportunity)
        == "OPEN_UNVERIFIED"
    )


def test_best_actionable_ignores_higher_unverified():
    opportunities = [
        make_opportunity(
            "High Score Unverified",
            24,
            "OPEN_UNVERIFIED",
        ),
        make_opportunity(
            "Lower Score Verified",
            23,
            "OPEN_VERIFIED",
        ),
    ]

    result = get_best_actionable_opportunity(
        opportunities
    )

    assert result is not None
    assert result["title"] == "Lower Score Verified"


def test_best_actionable_ignores_closed():
    opportunities = [
        make_opportunity(
            "Closed Job",
            30,
            "CLOSED",
        ),
        make_opportunity(
            "Verified Job",
            20,
            "OPEN_VERIFIED",
        ),
    ]

    result = get_best_actionable_opportunity(
        opportunities
    )

    assert result is not None
    assert result["title"] == "Verified Job"


def test_best_actionable_ignores_expired():
    opportunities = [
        make_opportunity(
            "Expired Job",
            30,
            "EXPIRED",
        ),
        make_opportunity(
            "Verified Job",
            20,
            "OPEN_VERIFIED",
        ),
    ]

    result = get_best_actionable_opportunity(
        opportunities
    )

    assert result is not None
    assert result["title"] == "Verified Job"


def test_best_actionable_ignores_broken_link():
    opportunities = [
        make_opportunity(
            "Broken Job",
            30,
            "APPLICATION_LINK_BROKEN",
        ),
        make_opportunity(
            "Verified Job",
            20,
            "OPEN_VERIFIED",
        ),
    ]

    result = get_best_actionable_opportunity(
        opportunities
    )

    assert result is not None
    assert result["title"] == "Verified Job"


def test_no_verified_returns_none():
    opportunities = [
        make_opportunity(
            "Unverified Job",
            25,
            "OPEN_UNVERIFIED",
        ),
        make_opportunity(
            "Closed Job",
            20,
            "CLOSED",
        ),
    ]

    assert (
        get_best_actionable_opportunity(
            opportunities
        )
        is None
    )


def test_top_unverified_returns_first_unverified():
    opportunities = [
        make_opportunity(
            "Verified Job",
            25,
            "OPEN_VERIFIED",
        ),
        make_opportunity(
            "Top Unverified",
            24,
            "OPEN_UNVERIFIED",
        ),
        make_opportunity(
            "Lower Unverified",
            20,
            "OPEN_UNVERIFIED",
        ),
    ]

    result = get_top_unverified_opportunity(
        opportunities
    )

    assert result is not None
    assert result["title"] == "Top Unverified"


def test_no_unverified_returns_none():
    opportunities = [
        make_opportunity(
            "Verified Job",
            25,
            "OPEN_VERIFIED",
        ),
    ]

    assert (
        get_top_unverified_opportunity(
            opportunities
        )
        is None
    )


def test_generate_verification_actions():
    opportunity = make_opportunity(
        "Example Internship",
        24,
        "OPEN_UNVERIFIED",
    )

    actions = generate_verification_actions(
        opportunity
    )

    assert len(actions) == 3
    assert "Example Internship" in actions[0]
    assert "Verify" in actions[0]
    assert "https://example.com/Example Internship" in actions[1]


def test_generate_verification_actions_none():
    assert generate_verification_actions(None) == []