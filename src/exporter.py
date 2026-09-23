import csv
import json
from pathlib import Path
from typing import Any

from ranking import (
    get_best_actionable_opportunity,
    get_top_unverified_opportunity,
)


def save_to_json(
    data: Any,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def save_to_csv(
    opportunities: list[dict[str, Any]],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "title",
        "type",
        "where",
        "date_deadline",
        "why_fit",
        "next_step",
        "source_link",
        "relevance",
        "beginner_fit",
        "career_value",
        "practicality",
        "university_fit",
        "total_score",
    ]

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for item in opportunities:
            row = {
                field: item.get(field, "")
                for field in fieldnames
            }

            writer.writerow(row)


def append_opportunity_details(
    lines: list[str],
    opportunity: dict[str, Any],
) -> None:
    lines.append(
        f"**Title:** "
        f"{opportunity.get('title', 'N/A')}"
    )

    lines.append(
        f"**Type:** "
        f"{opportunity.get('type', 'N/A')}"
    )

    lines.append(
        f"**Where:** "
        f"{opportunity.get('where', 'N/A')}"
    )

    lines.append(
        f"**Date/Deadline:** "
        f"{opportunity.get('date_deadline', 'N/A')}"
    )

    lines.append(
        f"**Total Score:** "
        f"{opportunity.get('total_score', 'N/A')}"
    )

    lines.append(
        f"**Why fit:** "
        f"{opportunity.get('why_fit', 'N/A')}"
    )

    lines.append(
        f"**Next step:** "
        f"{opportunity.get('next_step', 'N/A')}"
    )

    lines.append(
        f"**Source link:** "
        f"{opportunity.get('source_link', 'N/A')}"
    )

    verification = opportunity.get(
        "verification",
        {},
    )

    if verification:
        lines.append(
            f"**Application Status:** "
            f"{verification.get(
                'application_status',
                'OPEN_UNVERIFIED',
            )}"
        )

        employer_apply_url = verification.get(
            "employer_apply_url",
            "",
        )

        if employer_apply_url:
            lines.append(
                f"**Employer Apply URL:** "
                f"{employer_apply_url}"
            )

        application_link_status = (
            verification.get(
                "application_link_status",
                "",
            )
        )

        if application_link_status:
            lines.append(
                f"**Application Link Status:** "
                f"{application_link_status}"
            )

        lines.append(
            f"**Last Verified:** "
            f"{verification.get(
                'last_verified_at',
                'N/A',
            )}"
        )


def save_markdown_summary(
    opportunities: list[dict[str, Any]],
    actions: list[str],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines: list[str] = []

    lines.append(
        "# Weekly Opportunity Summary"
    )
    lines.append("")

    if not opportunities:
        lines.append(
            "No opportunities found."
        )

    else:
        best_actionable = (
            get_best_actionable_opportunity(
                opportunities
            )
        )

        top_unverified = (
            get_top_unverified_opportunity(
                opportunities
            )
        )

        # -----------------------------------------------------
        # Best Actionable Opportunity
        # -----------------------------------------------------
        lines.append(
            "## Best Actionable Opportunity"
        )
        lines.append("")

        if best_actionable:
            append_opportunity_details(
                lines,
                best_actionable,
            )
        else:
            lines.append(
                "No verified actionable opportunity "
                "is currently available."
            )

        lines.append("")

        # -----------------------------------------------------
        # Top Opportunity Needing Verification
        # -----------------------------------------------------
        lines.append(
            "## Top Opportunity Needing Verification"
        )
        lines.append("")

        if top_unverified:
            append_opportunity_details(
                lines,
                top_unverified,
            )
        else:
            lines.append(
                "No opportunity currently requires "
                "manual verification."
            )

        lines.append("")

        # -----------------------------------------------------
        # Ranked Opportunities
        # -----------------------------------------------------
        lines.append(
            "## Ranked Opportunities"
        )
        lines.append("")

        for i, item in enumerate(
            opportunities,
            start=1,
        ):
            lines.append(
                f"### {i}. "
                f"{item.get('title', 'N/A')}"
            )

            lines.append("")

            lines.append(
                f"- Type: "
                f"{item.get('type', 'N/A')}"
            )

            lines.append(
                f"- Where: "
                f"{item.get('where', 'N/A')}"
            )

            lines.append(
                f"- Date/Deadline: "
                f"{item.get('date_deadline', 'N/A')}"
            )

            lines.append(
                f"- Relevance: "
                f"{item.get('relevance', 'N/A')}"
            )

            lines.append(
                f"- Beginner Fit: "
                f"{item.get('beginner_fit', 'N/A')}"
            )

            lines.append(
                f"- Career Value: "
                f"{item.get('career_value', 'N/A')}"
            )

            lines.append(
                f"- Practicality: "
                f"{item.get('practicality', 'N/A')}"
            )

            lines.append(
                f"- University Fit: "
                f"{item.get('university_fit', 'N/A')}"
            )

            lines.append(
                f"- Total Score: "
                f"{item.get('total_score', 'N/A')}"
            )

            verification = item.get(
                "verification",
                {},
            )

            if verification:
                lines.append(
                    f"- Application Status: "
                    f"{verification.get(
                        'application_status',
                        'OPEN_UNVERIFIED',
                    )}"
                )

                employer_apply_url = (
                    verification.get(
                        "employer_apply_url",
                        "",
                    )
                )

                if employer_apply_url:
                    lines.append(
                        f"- Employer Apply URL: "
                        f"{employer_apply_url}"
                    )

                application_link_status = (
                    verification.get(
                        "application_link_status",
                        "",
                    )
                )

                if application_link_status:
                    lines.append(
                        f"- Application Link Status: "
                        f"{application_link_status}"
                    )

                lines.append(
                    f"- Last Verified: "
                    f"{verification.get(
                        'last_verified_at',
                        'N/A',
                    )}"
                )

            lines.append(
                f"- Why fit: "
                f"{item.get('why_fit', 'N/A')}"
            )

            lines.append(
                f"- Next step: "
                f"{item.get('next_step', 'N/A')}"
            )

            lines.append(
                f"- Source link: "
                f"{item.get('source_link', 'N/A')}"
            )

            lines.append("")

    # ---------------------------------------------------------
    # Recommended Actions
    # ---------------------------------------------------------
    if opportunities:
        best_actionable = (
            get_best_actionable_opportunity(
                opportunities
            )
        )

        if best_actionable:
            lines.append(
                "## Next 3 Actions"
            )
        else:
            lines.append(
                "## Verification Actions"
            )
    else:
        lines.append(
            "## Next Actions"
        )

    lines.append("")

    if actions:
        for i, action in enumerate(
            actions,
            start=1,
        ):
            lines.append(
                f"{i}. {action}"
            )
    else:
        lines.append(
            "No actions available."
        )

    lines.append("")

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )