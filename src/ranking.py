from typing import Any

try:
    from .parser import parse_opportunities_file, normalize_title
except ImportError:
    from parser import parse_opportunities_file, normalize_title


def deduplicate_opportunities(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
            existing_score = existing.get("total_score", -1)
            if existing_score is None:
                existing_score = -1

            if current_score > existing_score:
                best_by_title[norm_title] = item

    return list(best_by_title.values())


def sort_opportunities(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        opportunities,
        key=lambda item: item.get("total_score", -1) if item.get("total_score") is not None else -1,
        reverse=True,
    )


def get_best_opportunity(opportunities: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not opportunities:
        return None
    return opportunities[0]


def generate_next_actions(best: dict[str, Any] | None) -> list[str]:
    if not best:
        return [
            "Review the latest opportunity scan results.",
            "Check if any verified events need manual follow-up.",
            "Update memory with the current weekly status.",
        ]

    title = best.get("title", "this opportunity")
    source_link = best.get("source_link", "")
    date_deadline = best.get("date_deadline", "the event date")
    next_step = best.get("next_step", "Check the details and prepare to attend.")

    return [
        f"Open the source link for '{title}' and confirm the key details: {source_link}",
        f"Add '{title}' to your calendar and note the date/time: {date_deadline}",
        f"Complete this next step: {next_step}",
    ]