from datetime import date
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)


from archive_expired_opportunities import (
    classify_lifecycle,
)


def test_past_event_is_expired():
    status, _ = classify_lifecycle(
        "Sunday, August 9, 2026",
        today=date(2026, 8, 29),
    )

    assert status == "expired"


def test_future_event_is_active():
    status, _ = classify_lifecycle(
        "22 September 2026",
        today=date(2026, 8, 29),
    )

    assert status == "active"


def test_ongoing_application_is_active():
    status, _ = classify_lifecycle(
        "Applications are ongoing",
        today=date(2026, 8, 29),
    )

    assert status == "active"


def test_register_of_interest_is_active():
    status, _ = classify_lifecycle(
        "Register of interest open now; "
        "2027 deadline not yet published",
        today=date(2026, 8, 29),
    )

    assert status == "active"


def test_unknown_date_goes_to_review():
    status, _ = classify_lifecycle(
        "Summer 2026/2027",
        today=date(2026, 8, 29),
    )

    assert status == "uncertain"


def test_date_range_uses_end_date():
    status, _ = classify_lifecycle(
        "August 5-10, 2026",
        today=date(2026, 8, 29),
    )

    assert status == "expired"


def test_date_range_future_is_active():
    status, _ = classify_lifecycle(
        "September 5-10, 2026",
        today=date(2026, 8, 29),
    )

    assert status == "active"


def test_title_year_can_resolve_date_without_year():
    status, _ = classify_lifecycle(
        "Sat, Sep 12, 9:30 AM",
        title="MIT Open Day 2026",
        today=date(2026, 8, 29),
    )

    assert status == "active"

def test_expired_and_active_entries_separate_correctly():
    active_status, _ = classify_lifecycle(
        "30 November 2026",
        title="Future Tech Event 2026",
        today=date(2026, 9, 8),
    )

    expired_status, _ = classify_lifecycle(
        "30 August 2026",
        title="Old Tech Event 2026",
        today=date(2026, 9, 8),
    )

    assert active_status == "active"
    assert expired_status == "expired"