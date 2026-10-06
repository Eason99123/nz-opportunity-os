import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

from application_repository import (
    add_application,
    load_applications,
    replace_application,
    save_applications,
)


def make_application():
    return {
        "company": "Auckland Council",
        "title": "Software Engineering Intern",
        "source_link": "https://example.com/job/123",
        "status": "APPLIED",
        "applied_at": "2026-10-05",
        "last_updated_at": "2026-10-05",
        "notes": "",
    }


def test_load_missing_file_returns_empty_list(tmp_path):
    path = tmp_path / "applications.json"

    assert load_applications(path) == []


def test_save_and_load_applications(tmp_path):
    path = tmp_path / "applications.json"
    applications = [make_application()]

    save_applications(applications, path)

    assert load_applications(path) == applications


def test_save_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "applications.json"

    save_applications([make_application()], path)

    assert path.exists()


def test_saved_file_is_valid_json(tmp_path):
    path = tmp_path / "applications.json"

    save_applications([make_application()], path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data[0]["company"] == "Auckland Council"


def test_load_rejects_non_list_json(tmp_path):
    path = tmp_path / "applications.json"
    path.write_text(
        '{"company": "Example"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_applications(path)


def test_add_application(tmp_path):
    path = tmp_path / "applications.json"
    application = make_application()

    add_application(application, path)

    assert load_applications(path) == [application]


def test_add_application_rejects_duplicate_source_link(tmp_path):
    path = tmp_path / "applications.json"
    application = make_application()

    add_application(application, path)

    with pytest.raises(ValueError):
        add_application(application, path)


def test_replace_application(tmp_path):
    path = tmp_path / "applications.json"
    application = make_application()
    add_application(application, path)

    updated = dict(application)
    updated["status"] = "INTERVIEW"
    updated["notes"] = "Interview invitation received."

    replace_application(updated, path)

    saved = load_applications(path)

    assert len(saved) == 1
    assert saved[0]["status"] == "INTERVIEW"
    assert saved[0]["notes"] == "Interview invitation received."


def test_replace_missing_application_raises_error(tmp_path):
    path = tmp_path / "applications.json"

    with pytest.raises(ValueError):
        replace_application(make_application(), path)