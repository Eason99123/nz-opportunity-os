from typing import Any

try:
    from .parser import parse_opportunities_file, normalize_title
except ImportError:
    from parser import parse_opportunities_file, normalize_title


OPEN_VERIFIED = "OPEN_VERIFIED"
OPEN_UNVERIFIED = "OPEN_UNVERIFIED"


def deduplicate_opportunities(
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    best_by_title: dict[str, dict[str, Any]] = {}

    for item in opportunities:
        title = item.get("title")

        if not title:
            continue

        norm_title = normalize_title(title)

        current_score = item.get("total_score", -1)

        if current_score is None:
            current_score = -1

        if norm_title not in best_by_title:
            best_by_title[norm_title] = item

        else:
            existing = best_by_title[norm_title]

            existing_score = existing.get(
                "total_score",
                -1,
            )

            if existing_score is None:
                existing_score = -1

            if current_score > existing_score:
                best_by_title[norm_title] = item

    return list(best_by_title.values())


def sort_opportunities(
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        opportunities,
        key=lambda item: (
            item.get("total_score", -1)
            if item.get("total_score") is not None
            else -1
        ),
        reverse=True,
    )


def get_best_opportunity(
    opportunities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not opportunities:
        return None

    return opportunities[0]


def get_verification_status(
    opportunity: dict[str, Any],
) -> str:
    verification = opportunity.get("verification")

    if not isinstance(verification, dict):
        return OPEN_UNVERIFIED

    status = verification.get("application_status")

    if not isinstance(status, str):
        return OPEN_UNVERIFIED

    status = status.strip().upper()

    if not status:
        return OPEN_UNVERIFIED

    return status


def get_best_actionable_opportunity(
    opportunities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for opportunity in opportunities:
        if (
            get_verification_status(opportunity)
            == OPEN_VERIFIED
        ):
            return opportunity

    return None


def get_top_unverified_opportunity(
    opportunities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for opportunity in opportunities:
        if (
            get_verification_status(opportunity)
            == OPEN_UNVERIFIED
        ):
            return opportunity

    return None


def generate_next_actions(
    best: dict[str, Any] | None,
) -> list[str]:
    if not best:
        return [
            "Review the latest opportunity scan results.",
            "Check if any verified events need manual follow-up.",
            "Update memory with the current weekly status.",
        ]

    title = best.get(
        "title",
        "this opportunity",
    )

    source_link = best.get(
        "source_link",
        "",
    )

    date_deadline = best.get(
        "date_deadline",
        "the event date",
    )

    next_step = best.get(
        "next_step",
        "Check the details and prepare to attend.",
    )

    return [
        (
            f"Open the source link for '{title}' "
            f"and confirm the key details: {source_link}"
        ),
        (
            f"Add '{title}' to your calendar and "
            f"note the date/time: {date_deadline}"
        ),
        f"Complete this next step: {next_step}",
    ]


def generate_verification_actions(
    opportunity: dict[str, Any] | None,
) -> list[str]:
    if not opportunity:
        return []

    title = opportunity.get(
        "title",
        "this opportunity",
    )

    source_link = opportunity.get(
        "source_link",
        "",
    )

    return [
        (
            f"Verify the official listing for "
            f"'{title}' before taking action."
        ),
        (
            f"Check whether the opportunity is still "
            f"open: {source_link}"
        ),
        (
            "Confirm the official application or "
            "registration link before proceeding."
        ),
    ]