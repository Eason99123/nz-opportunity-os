import json
from copy import deepcopy
from pathlib import Path


DEFAULT_APPLICATIONS_FILE = (
    Path(__file__).resolve().parents[1]
    / "opportunities"
    / "applications.json"
)


def load_applications(json_file=DEFAULT_APPLICATIONS_FILE):
    path = Path(json_file)

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Applications file must contain a JSON list.")

    return deepcopy(data)


def save_applications(
    applications,
    json_file=DEFAULT_APPLICATIONS_FILE,
):
    path = Path(json_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            applications,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return path


def add_application(
    application,
    json_file=DEFAULT_APPLICATIONS_FILE,
):
    applications = load_applications(json_file)

    source_link = application.get("source_link", "").strip()

    if source_link:
        for existing in applications:
            if existing.get("source_link", "").strip() == source_link:
                raise ValueError(
                    "Application with this source link already exists."
                )

    applications.append(deepcopy(application))
    save_applications(applications, json_file)

    return deepcopy(application)


def replace_application(
    updated_application,
    json_file=DEFAULT_APPLICATIONS_FILE,
):
    applications = load_applications(json_file)

    source_link = updated_application.get("source_link", "").strip()

    if not source_link:
        raise ValueError(
            "Application must have a source link to be replaced."
        )

    for index, application in enumerate(applications):
        if application.get("source_link", "").strip() == source_link:
            applications[index] = deepcopy(updated_application)
            save_applications(applications, json_file)
            return deepcopy(updated_application)

    raise ValueError("Application not found.")