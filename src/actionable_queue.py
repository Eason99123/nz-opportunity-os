from __future__ import annotations

from typing import Any


OPEN_VERIFIED = "OPEN_VERIFIED"

BLOCKED_STATUSES = {
    "CLOSED",
    "APPLICATION_LINK_BROKEN",
    "EXPIRED",
}


def get_application_status(
    opportunity: dict[str, Any],
) -> str:
    verification = opportunity.get("verification")

    if not isinstance(verification, dict):
        return "OPEN_UNVERIFIED"

    status = verification.get("application_status")

    if not isinstance(status, str) or not status.strip():
        return "OPEN_UNVERIFIED"

    return status.strip().upper()


def get_actionability(
    opportunity: dict[str, Any],
) -> dict[str, Any]:
    status = get_application_status(opportunity)

    if status == OPEN_VERIFIED:
        return {
            "actionable": True,
            "status": status,
            "reason": "Opportunity is verified and open.",
        }

    if status == "OPEN_UNVERIFIED":
        return {
            "actionable": False,
            "status": status,
            "reason": "Opportunity has not been verified yet.",
        }

    if status == "CLOSED":
        return {
            "actionable": False,
            "status": status,
            "reason": "Official listing is closed or no longer present.",
        }

    if status == "APPLICATION_LINK_BROKEN":
        return {
            "actionable": False,
            "status": status,
            "reason": "Application link is broken.",
        }

    if status == "EXPIRED":
        return {
            "actionable": False,
            "status": status,
            "reason": "Opportunity has expired.",
        }

    return {
        "actionable": False,
        "status": status,
        "reason": f"Unknown verification status: {status}.",
    }


def is_actionable(
    opportunity: dict[str, Any],
) -> bool:
    return get_actionability(opportunity)["actionable"]


def build_actionable_queue(
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        opportunity.copy()
        for opportunity in opportunities
        if is_actionable(opportunity)
    ]


def build_queue_summary(
    opportunities: list[dict[str, Any]],
) -> dict[str, int]:
    actionable = 0
    needs_verification = 0
    blocked = 0

    for opportunity in opportunities:
        result = get_actionability(opportunity)

        if result["actionable"]:
            actionable += 1
        elif result["status"] == "OPEN_UNVERIFIED":
            needs_verification += 1
        else:
            blocked += 1

    return {
        "total": len(opportunities),
        "actionable": actionable,
        "needs_verification": needs_verification,
        "blocked": blocked,
    }