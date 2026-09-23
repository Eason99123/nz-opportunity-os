import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from exporter import save_markdown_summary, save_to_csv, save_to_json


def make_opportunity(
    title: str,
    status: str,
    total_score: int = 23,
) -> dict:
    return {
        "title": title,
        "type": "Tech Meetup",
        "where": "Microsoft, Auckland",
        "date_deadline": "Monday, May 4, 5:30 PM",
        "why_fit": "Good networking opportunity and AI-related learning.",
        "next_step": "Register on Eventbrite.",
        "source_link": "https://example.com/peak",
        "relevance": 5,
        "beginner_fit": 4,
        "career_value": 4,
        "practicality": 5,
        "university_fit": 5,
        "total_score": total_score,
        "verification": {
            "application_status": status,
            "employer_apply_url": "",
            "last_verified_at": "2026-09-23",
            "application_link_status": "",
            "official_listing_present": None,
        },
    }


def test_save_to_json_creates_file_and_writes_content(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "output.json"

    data = {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "count": 1,
        "best_opportunity": {
            "title": "Peak Performance & AI - May Meetup"
        },
        "next_actions": [
            "Register on Eventbrite."
        ],
        "opportunities": [
            {
                "title": "Peak Performance & AI - May Meetup",
                "total_score": 23,
            }
        ],
    }

    save_to_json(data, output_file)

    assert output_file.exists()

    content = output_file.read_text(
        encoding="utf-8"
    )

    assert "Peak Performance & AI - May Meetup" in content
    assert '"count": 1' in content


def test_save_to_csv_creates_file_and_writes_rows(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "output.csv"

    opportunities = [
        make_opportunity(
            "Peak Performance & AI - May Meetup",
            "OPEN_VERIFIED",
        )
    ]

    save_to_csv(
        opportunities,
        output_file,
    )

    assert output_file.exists()

    content = output_file.read_text(
        encoding="utf-8"
    )

    assert "title,type,where" in content
    assert "Peak Performance & AI - May Meetup" in content
    assert "Microsoft, Auckland" in content


def test_save_markdown_summary_creates_readable_summary(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "summary.md"

    opportunities = [
        make_opportunity(
            "Peak Performance & AI - May Meetup",
            "OPEN_VERIFIED",
        )
    ]

    actions = [
        "Open the source link.",
        "Add the event to your calendar.",
        "Register on Eventbrite.",
    ]

    save_markdown_summary(
        opportunities,
        actions,
        output_file,
    )

    assert output_file.exists()

    content = output_file.read_text(
        encoding="utf-8"
    )

    assert "# Weekly Opportunity Summary" in content
    assert "## Best Actionable Opportunity" in content
    assert "Peak Performance & AI - May Meetup" in content
    assert "## Next 3 Actions" in content
    assert "Register on Eventbrite." in content
    assert "Application Status: OPEN_VERIFIED" in content


def test_open_unverified_is_not_best_actionable_opportunity(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "summary.md"

    opportunities = [
        make_opportunity(
            "Unverified High Score Opportunity",
            "OPEN_UNVERIFIED",
            total_score=25,
        )
    ]

    actions = [
        "Verify the official listing.",
        "Check whether the opportunity is still open.",
        "Confirm the official application link.",
    ]

    save_markdown_summary(
        opportunities,
        actions,
        output_file,
    )

    content = output_file.read_text(
        encoding="utf-8"
    )

    assert "## Best Actionable Opportunity" in content
    assert (
        "No verified actionable opportunity is currently available."
        in content
    )

    assert "## Top Opportunity Needing Verification" in content
    assert "Unverified High Score Opportunity" in content
    assert "Application Status: OPEN_UNVERIFIED" in content


def test_verified_opportunity_beats_unverified_for_actionable_section(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "summary.md"

    opportunities = [
        make_opportunity(
            "High Score Unverified Opportunity",
            "OPEN_UNVERIFIED",
            total_score=30,
        ),
        make_opportunity(
            "Verified Opportunity",
            "OPEN_VERIFIED",
            total_score=20,
        ),
    ]

    actions = [
        "Open the verified opportunity.",
        "Review the application requirements.",
        "Apply through the official link.",
    ]

    save_markdown_summary(
        opportunities,
        actions,
        output_file,
    )

    content = output_file.read_text(
        encoding="utf-8"
    )

    assert "## Best Actionable Opportunity" in content
    assert "Verified Opportunity" in content
    assert "Application Status: OPEN_VERIFIED" in content

    assert "## Top Opportunity Needing Verification" in content
    assert "High Score Unverified Opportunity" in content


def test_blocked_opportunity_is_not_best_actionable(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "summary.md"

    opportunities = [
        make_opportunity(
            "Closed Opportunity",
            "CLOSED",
            total_score=30,
        ),
        make_opportunity(
            "Expired Opportunity",
            "EXPIRED",
            total_score=20,
        ),
        make_opportunity(
            "Broken Application Opportunity",
            "APPLICATION_LINK_BROKEN",
            total_score=8,
        ),
    ]

    actions = []

    save_markdown_summary(
        opportunities,
        actions,
        output_file,
    )

    content = output_file.read_text(
        encoding="utf-8"
    )

    # No blocked opportunity may become the recommended
    # actionable opportunity.
    assert (
        "No verified actionable opportunity is currently available."
        in content
    )

    # Blocked opportunities should still remain visible in the
    # ranked report for transparency.
    assert "Closed Opportunity" in content
    assert "Expired Opportunity" in content
    assert "Broken Application Opportunity" in content

    # Their verification statuses should also remain visible.
    assert "CLOSED" in content
    assert "EXPIRED" in content
    assert "APPLICATION_LINK_BROKEN" in content

def test_markdown_contains_verification_actions_for_unverified(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "summary.md"

    opportunities = [
        make_opportunity(
            "Opportunity To Verify",
            "OPEN_UNVERIFIED",
        )
    ]

    actions = [
        "Verify the official listing.",
        "Check whether the opportunity is still open.",
        "Confirm the official application link.",
    ]

    save_markdown_summary(
        opportunities,
        actions,
        output_file,
    )

    content = output_file.read_text(
        encoding="utf-8"
    )

    assert "## Verification Actions" in content
    assert "Verify the official listing." in content
    assert "Check whether the opportunity is still open." in content
    assert "Confirm the official application link." in content