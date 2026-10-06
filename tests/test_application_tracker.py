from copy import deepcopy
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

from application_tracker import (
    create_application,
    find_application_by_source_link,
    update_application_status,
)


def make_application():
    return create_application(
        company="Auckland Council",
        title="Software Engineering Intern",
        source_link="https://example.com/auckland-council",
        applied_at="2026-10-05",
    )


def test_create_application():
    application = make_application()

    assert application["company"] == "Auckland Council"
    assert application["title"] == "Software Engineering Intern"
    assert (
        application["source_link"]
        == "https://example.com/auckland-council"
    )
    assert application["status"] == "APPLIED"
    assert application["applied_at"] == "2026-10-05"
    assert application["last_updated_at"] == "2026-10-05"
    assert application["notes"] == ""


def test_create_application_normalizes_status():
    application = create_application(
        company="Serko",
        title="Intern Software Engineer",
        applied_at="2026-10-04",
        status="interview",
    )

    assert application["status"] == "INTERVIEW"


def test_create_application_rejects_invalid_status():
    with pytest.raises(ValueError):
        create_application(
            company="Example",
            title="Intern",
            applied_at="2026-10-05",
            status="UNKNOWN",
        )


def test_update_application_status():
    application = make_application()

    updated = update_application_status(
        application,
        status="INTERVIEW",
        last_updated_at="2026-10-20",
        notes="Interview invitation received.",
    )

    assert updated["status"] == "INTERVIEW"
    assert updated["last_updated_at"] == "2026-10-20"
    assert updated["notes"] == "Interview invitation received."


def test_update_application_does_not_mutate_original():
    application = make_application()
    original = deepcopy(application)

    update_application_status(
        application,
        status="REJECTED",
        last_updated_at="2026-10-20",
    )

    assert application == original


def test_update_application_rejects_invalid_status():
    application = make_application()

    with pytest.raises(ValueError):
        update_application_status(
            application,
            status="UNKNOWN",
            last_updated_at="2026-10-20",
        )


def test_find_application_by_source_link():
    first = make_application()

    second = create_application(
        company="Serko",
        title="Intern Software Engineer",
        source_link="https://example.com/serko",
        applied_at="2026-10-04",
    )

    result = find_application_by_source_link(
        [first, second],
        "https://example.com/serko",
    )

    assert result is not None
    assert result["company"] == "Serko"


def test_find_application_returns_none_when_missing():
    application = make_application()

    result = find_application_by_source_link(
        [application],
        "https://example.com/missing",
    )

    assert result is None


def test_find_application_returns_copy():
    application = make_application()

    result = find_application_by_source_link(
        [application],
        application["source_link"],
    )

    assert result is not application
    assert result == application