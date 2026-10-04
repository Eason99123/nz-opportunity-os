from __future__ import annotations

from copy import deepcopy
from typing import Any


VALID_STATUSES = {
    "OPEN_VERIFIED",
    "OPEN_UNVERIFIED",
    "CLOSED",
    "APPLICATION_LINK_BROKEN",
    "EXPIRED",
}


def apply_verification_result(
    opportunity: dict[str, Any],
    *,
    application_status: str,
    employer_apply_url: str | None = None,
    application_link_status: str | None = None,
    official_listing_present: bool | None = None,
    verification_reason: str | None = None,
    last_verified_at: str | None = None,
) -> dict[str, Any]:
    """
    Return a copy of an opportunity with a verification result applied.

    The original opportunity is never mutated.
    """

    status = application_status.strip().upper()

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid application status: {application_status}"
        )

    updated = deepcopy(opportunity)

    existing_verification = updated.get("verification")

    if isinstance(existing_verification, dict):
        verification = deepcopy(existing_verification)
    else:
        verification = {}

    verification["application_status"] = status

    if employer_apply_url is not None:
        verification["employer_apply_url"] = employer_apply_url

    if application_link_status is not None:
        verification["application_link_status"] = (
            application_link_status
        )

    if official_listing_present is not None:
        verification["official_listing_present"] = (
            official_listing_present
        )

    if verification_reason is not None:
        verification["verification_reason"] = (
            verification_reason
        )

    if last_verified_at is not None:
        verification["last_verified_at"] = last_verified_at

    updated["verification"] = verification

    return updated


def apply_verification_results(
    opportunities: list[dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Apply verification results to opportunities by source_link.

    Opportunities without a matching result are copied unchanged.
    """

    updated_opportunities = []

    for opportunity in opportunities:
        source_link = opportunity.get("source_link")
        result = results.get(source_link)

        if result is None:
            updated_opportunities.append(
                deepcopy(opportunity)
            )
            continue

        updated = apply_verification_result(
            opportunity,
            application_status=result[
                "application_status"
            ],
            employer_apply_url=result.get(
                "employer_apply_url"
            ),
            application_link_status=result.get(
                "application_link_status"
            ),
            official_listing_present=result.get(
                "official_listing_present"
            ),
            verification_reason=result.get(
                "verification_reason"
            ),
            last_verified_at=result.get(
                "last_verified_at"
            ),
        )

        updated_opportunities.append(updated)

    return updated_opportunities