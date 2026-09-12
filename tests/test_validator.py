from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from validate_opportunities import (
    is_generic_url,
    normalize_url,
    title_similarity,
)

from validate_opportunities import (
    clearly_distinct_events,
)

def test_seek_generic_search_page_is_rejected():
    url = (
        "https://nz.seek.com/"
        "internship-opportunities-for-computer-science-students-jobs/"
        "in-All-Auckland"
    )

    assert is_generic_url(url) is True


def test_seek_direct_job_page_is_allowed():
    url = "https://www.seek.co.nz/job/12345678"

    assert is_generic_url(url) is False


def test_tracking_parameters_are_removed():
    original = (
        "https://www.eventbrite.com/e/test-event"
        "?aff=ebdssbdestsearch"
    )

    normalized = normalize_url(original)

    assert normalized == (
        "https://www.eventbrite.com/e/test-event"
    )


def test_ai_hackathon_titles_are_similar():
    first = "Aotearoa AI Hackathon Festival 2026"
    second = "Aotearoa AI Hackathon Festival Auckland"

    assert title_similarity(first, second) >= 0.82


def test_velocity_prizegiving_is_not_exact_duplicate():
    first = "Velocity $100k Challenge 2026"
    second = "Velocity $100k Challenge Prizegiving 2026"

    assert title_similarity(first, second) < 0.90

def test_different_sessions_are_distinct():
    first = (
        "Careers in the Innovation Ecosystem Session 1"
    )

    second = (
        "Careers in the Innovation Ecosystem Session 2"
    )

    assert clearly_distinct_events(
        first,
        second,
    ) is True


def test_workshop_and_prizegiving_are_distinct():
    first = (
        "Velocity $100k Challenge Workshop"
    )

    second = (
        "Velocity $100k Challenge Grand Final Prizegiving 2026"
    )

    assert clearly_distinct_events(
        first,
        second,
    ) is True


def test_same_hackathon_names_are_not_distinct():
    first = (
        "Aotearoa AI Hackathon Festival 2026"
    )

    second = (
        "Aotearoa AI Hackathon Festival Auckland"
    )

    assert clearly_distinct_events(
        first,
        second,
    ) is False