import json
import sys
from pathlib import Path
from typing import Any

from verification_updater import apply_verification_result


VALID_STATUSES = [
    "OPEN_VERIFIED",
    "CLOSED",
    "APPLICATION_LINK_BROKEN",
    "EXPIRED",
]


def load_payload(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path.resolve()}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "JSON root must be an object."
        )

    return data


def save_payload(
    payload: dict[str, Any],
    file_path: Path,
) -> None:
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )


def get_opportunities_needing_verification(
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = []

    for opportunity in opportunities:
        verification = opportunity.get(
            "verification",
            {},
        )

        status = verification.get(
            "application_status",
            "OPEN_UNVERIFIED",
        )

        if status == "OPEN_UNVERIFIED":
            result.append(opportunity)

    return result


def display_opportunities(
    opportunities: list[dict[str, Any]],
) -> None:

    print()
    print("Opportunities Needing Verification")
    print("=" * 40)

    for index, opportunity in enumerate(
        opportunities,
        start=1,
    ):
        title = opportunity.get(
            "title",
            "Untitled Opportunity",
        )

        score = opportunity.get(
            "total_score",
            "N/A",
        )

        source_link = opportunity.get(
            "source_link",
            "N/A",
        )

        print()
        print(f"{index}. {title}")
        print("   Status: OPEN_UNVERIFIED")
        print(f"   Score: {score}")
        print(f"   Source: {source_link}")


def select_opportunity(
    opportunities: list[dict[str, Any]],
) -> int:

    while True:
        raw_value = input(
            "\nSelect opportunity: "
        ).strip()

        try:
            selection = int(raw_value)
        except ValueError:
            print(
                "Please enter a valid number."
            )
            continue

        if 1 <= selection <= len(opportunities):
            return selection - 1

        print(
            "Selection is out of range."
        )


def display_status_options() -> None:
    print()
    print("Verification result:")

    for index, status in enumerate(
        VALID_STATUSES,
        start=1,
    ):
        print(
            f"{index}. {status}"
        )


def select_status() -> str:

    while True:
        raw_value = input(
            "\nSelect status: "
        ).strip()

        try:
            selection = int(raw_value)
        except ValueError:
            print(
                "Please enter a valid number."
            )
            continue

        if 1 <= selection <= len(VALID_STATUSES):
            return VALID_STATUSES[
                selection - 1
            ]

        print(
            "Selection is out of range."
        )


def ask_yes_no(prompt: str) -> bool:

    while True:
        value = input(
            f"{prompt} [y/n]: "
        ).strip().lower()

        if value in {"y", "yes"}:
            return True

        if value in {"n", "no"}:
            return False

        print(
            "Please enter y or n."
        )


def main() -> None:

    if len(sys.argv) > 2:
        print(
            "Usage: python src/verification_cli.py "
            "[json_file]"
        )
        sys.exit(1)

    json_file = (
        Path(sys.argv[1])
        if len(sys.argv) == 2
        else Path("opportunities")
        / "deduplicated_ranked_output.json"
    )

    try:
        payload = load_payload(
            json_file
        )

        opportunities = payload.get(
            "opportunities",
            [],
        )

        if not isinstance(
            opportunities,
            list,
        ):
            raise ValueError(
                "'opportunities' must be a list."
            )

        pending = (
            get_opportunities_needing_verification(
                opportunities
            )
        )

        if not pending:
            print(
                "No opportunities currently "
                "need verification."
            )
            return

        display_opportunities(
            pending
        )

        selected_index = (
            select_opportunity(
                pending
            )
        )

        selected = pending[
            selected_index
        ]

        old_status = (
            selected.get(
                "verification",
                {},
            ).get(
                "application_status",
                "OPEN_UNVERIFIED",
            )
        )

        display_status_options()

        new_status = select_status()

        official_listing_present = (
            ask_yes_no(
                "Official listing present?"
            )
        )

        application_link_works = (
            ask_yes_no(
                "Application link works?"
            )
        )

        reason = input(
            "Verification reason: "
        ).strip()

        updated = apply_verification(
            selected,
            application_status=new_status,
            official_listing_present=(
                official_listing_present
            ),
            application_link_status=(
                "WORKING"
                if application_link_works
                else "BROKEN"
            ),
            verification_reason=reason,
        )

        for index, opportunity in enumerate(
            opportunities
        ):
            if opportunity is selected:
                opportunities[index] = updated
                break

        payload["opportunities"] = (
            opportunities
        )

        save_payload(
            payload,
            json_file,
        )

        print()
        print("Updated successfully:")
        print(
            updated.get(
                "title",
                "Untitled Opportunity",
            )
        )
        print(
            f"{old_status} -> {new_status}"
        )
        print(
            f"Saved to: {json_file.resolve()}"
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ) as error:
        print(
            f"Error: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()