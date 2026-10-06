from __future__ import annotations

from copy import deepcopy
from typing import Any


VALID_APPLICATION_STATUSES = {
    "APPLIED",
    "ASSESSMENT",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "WITHDRAWN",
    "NO_RESPONSE",
}


def create_application(
    *,
    company: str,
    title: str,
    source_link: str = "",
    applied_at: str,
    status: str = "APPLIED",
    notes: str = "",
) -> dict[str, Any]:
    """
    Create a new application record.
    """

    normalized_status = status.strip().upper()

    if normalized_status not in VALID_APPLICATION_STATUSES:
        raise ValueError(
            f"Invalid application status: {status}"
        )

    return {
        "company": company.strip(),
        "title": title.strip(),
        "source_link": source_link.strip(),
        "status": normalized_status,
        "applied_at": applied_at,
        "last_updated_at": applied_at,
        "notes": notes.strip(),
    }


def update_application_status(
    application: dict[str, Any],
    *,
    status: str,
    last_updated_at: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Return a copy of an application with its status updated.

    The original application is never mutated.
    """

    normalized_status = status.strip().upper()

    if normalized_status not in VALID_APPLICATION_STATUSES:
        raise ValueError(
            f"Invalid application status: {status}"
        )

    updated = deepcopy(application)

    updated["status"] = normalized_status
    updated["last_updated_at"] = last_updated_at

    if notes is not None:
        updated["notes"] = notes.strip()

    return updated


def find_application_by_source_link(
    applications: list[dict[str, Any]],
    source_link: str,
) -> dict[str, Any] | None:
    """
    Find an application by its opportunity source link.
    """

    for application in applications:
        if application.get("source_link") == source_link:
            return deepcopy(application)

    return None