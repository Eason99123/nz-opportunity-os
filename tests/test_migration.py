from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)


from validate_opportunities import (
    parse_entry,
    validate_entry,
)


def make_entry(
    title: str,
    source_link: str,
    date_deadline: str,
) -> dict[str, str]:
    return {
        "Title": title,
        "Type": "Test",
        "Where": "Auckland",
        "Date/Deadline": date_deadline,
        "Why fit": "Test opportunity.",
        "Next step": "Review.",
        "Source link": source_link,
        "Relevance": "5/5",
        "Beginner Fit": "5/5",
        "Career Value": "5/5",
        "Practicality": "5/5",
        "University Fit": "5/5",
        "Total Score": "25/25",
    }


def test_legacy_seek_search_page_is_rejected():
    seen = []

    entry = make_entry(
        "Fake Legacy Internship",
        (
            "https://nz.seek.com/"
            "internship-opportunities-for-computer-science-students-jobs/"
            "in-All-Auckland"
        ),
        "Summer 2026/2027",
    )

    result = validate_entry(
        entry,
        seen,
    )

    assert result["status"] == "rejected"


def test_direct_future_opportunity_can_pass_validation():
    seen = []

    entry = make_entry(
        "Valid Future Opportunity",
        "https://example.com/opportunity/123",
        "31 December 2026",
    )

    result = validate_entry(
        entry,
        seen,
    )

    assert result["status"] == "approved"


def test_exact_duplicate_is_rejected():
    seen = []

    first = make_entry(
        "Test Hackathon",
        "https://example.com/hackathon",
        "31 December 2026",
    )

    second = make_entry(
        "Test Hackathon",
        "https://example.com/hackathon?tracking=1",
        "31 December 2026",
    )

    first_result = validate_entry(
        first,
        seen,
    )

    second_result = validate_entry(
        second,
        seen,
    )

    assert first_result["status"] == "approved"
    assert second_result["status"] == "rejected"

def test_migration_validation_can_ignore_expired_date():
    seen = []

    entry = make_entry(
        "Old Valid Event",
        "https://example.com/event/old-valid-event",
        "9 August 2026",
    )

    result = validate_entry(
        entry,
        seen,
        check_date_status=False,
    )

    assert result["status"] == "approved"


def test_normal_validation_still_rejects_expired_date():
    seen = []

    entry = make_entry(
        "Old Valid Event",
        "https://example.com/event/old-valid-event",
        "9 August 2026",
    )

    result = validate_entry(
        entry,
        seen,
        check_date_status=True,
    )

    assert result["status"] == "rejected"


def test_migration_still_rejects_generic_seek_page():
    seen = []

    entry = make_entry(
        "Legacy Fake Internship",
        (
            "https://nz.seek.com/"
            "internship-opportunities-for-computer-science-students-jobs/"
            "in-All-Auckland"
        ),
        "Summer 2026/2027",
    )

    result = validate_entry(
        entry,
        seen,
        check_date_status=False,
    )

    assert result["status"] == "rejected"