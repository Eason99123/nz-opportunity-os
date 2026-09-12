from __future__ import annotations

import json
import re
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_BATCH_FILE = (
    PROJECT_ROOT
    / "incoming"
    / "openclaw_batch.txt"
)

ACTIVE_OUTPUT_FILE = (
    PROJECT_ROOT
    / "incoming"
    / "openclaw_active.txt"
)

UNCERTAIN_OUTPUT_FILE = (
    PROJECT_ROOT
    / "incoming"
    / "openclaw_lifecycle_review.txt"
)

ARCHIVE_DIR = (
    PROJECT_ROOT
    / "opportunities"
    / "archive"
)

STATUS_JSON = (
    PROJECT_ROOT
    / "logs"
    / "latest_archive_status.json"
)

STATUS_TXT = (
    PROJECT_ROOT
    / "logs"
    / "latest_archive_status.txt"
)


REQUIRED_FIELDS = [
    "Title",
    "Type",
    "Where",
    "Date/Deadline",
    "Why fit",
    "Next step",
    "Source link",
    "Relevance",
    "Beginner Fit",
    "Career Value",
    "Practicality",
    "University Fit",
    "Total Score",
]


MONTH_PATTERN = (
    r"(January|February|March|April|May|June|July|August|"
    r"September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
)


MONTH_NAMES = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def read_text_with_fallback(path: Path) -> str:
    for encoding in (
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "cp1252",
    ):
        try:
            return path.read_text(
                encoding=encoding
            )
        except UnicodeDecodeError:
            continue

    raise RuntimeError(
        f"Unable to decode file: {path}"
    )


def split_entries(text: str) -> list[str]:
    text = text.strip()

    if not text:
        return []

    if "===OPPORTUNITY===" in text:
        blocks = text.split(
            "===OPPORTUNITY==="
        )

        return [
            block.strip()
            for block in blocks
            if block.strip()
        ]

    starts = list(
        re.finditer(
            r"(?m)^Title:\s*",
            text,
        )
    )

    if not starts:
        return []

    entries = []

    for index, match in enumerate(starts):
        start = match.start()

        if index + 1 < len(starts):
            end = starts[index + 1].start()
        else:
            end = len(text)

        block = text[start:end].strip()

        if block:
            entries.append(block)

    return entries


def parse_entry(
    block: str,
) -> dict[str, str]:
    result: dict[str, str] = {}

    current_field = None

    for raw_line in block.splitlines():
        line = raw_line.rstrip()

        matched = False

        for field in REQUIRED_FIELDS:
            prefix = f"{field}:"

            if line.startswith(prefix):
                result[field] = (
                    line[len(prefix):].strip()
                )

                current_field = field
                matched = True
                break

        if matched:
            continue

        if (
            current_field
            and line.strip()
        ):
            result[current_field] = (
                result.get(
                    current_field,
                    "",
                )
                + " "
                + line.strip()
            ).strip()

    return result


def serialize_entry(
    entry: dict[str, str],
) -> str:
    lines = []

    for field in REQUIRED_FIELDS:
        if field in entry:
            lines.append(
                f"{field}: {entry[field]}"
            )

    return "\n".join(lines)


def write_entries(
    path: Path,
    entries: list[dict[str, str]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    blocks = [
        serialize_entry(entry)
        for entry in entries
    ]

    path.write_text(
        "\n\n===OPPORTUNITY===\n\n".join(
            blocks
        ),
        encoding="utf-8",
    )


def extract_year_from_title(
    title: str,
) -> int | None:
    match = re.search(
        r"\b(20\d{2})\b",
        title,
    )

    if not match:
        return None

    return int(
        match.group(1)
    )


def extract_explicit_dates(
    text: str,
    fallback_year: int | None = None,
) -> list[date]:
    found: list[date] = []

    def add_date(
        year: int,
        month_text: str,
        day: int,
    ) -> None:
        month_number = MONTH_NAMES.get(
            month_text.lower()
        )

        if not month_number:
            return

        try:
            parsed = date(
                year,
                month_number,
                day,
            )

            if parsed not in found:
                found.append(
                    parsed
                )

        except ValueError:
            pass

    # --------------------------------------------------------
    # 21 October 2026
    # --------------------------------------------------------

    pattern = (
        rf"\b(\d{{1,2}})\s+"
        rf"{MONTH_PATTERN}\s+"
        rf"(20\d{{2}})\b"
    )

    for match in re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    ):
        add_date(
            int(match.group(3)),
            match.group(2),
            int(match.group(1)),
        )

    # --------------------------------------------------------
    # October 21, 2026
    # October 21 2026
    # --------------------------------------------------------

    pattern = (
        rf"\b{MONTH_PATTERN}\s+"
        rf"(\d{{1,2}})"
        rf"(?:st|nd|rd|th)?"
        rf"[,]?\s+"
        rf"(20\d{{2}})\b"
    )

    for match in re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    ):
        add_date(
            int(match.group(3)),
            match.group(1),
            int(match.group(2)),
        )

    # --------------------------------------------------------
    # August 5-10, 2026
    # August 5–10, 2026
    # August 5 to 10, 2026
    #
    # Use the end date of the range.
    # --------------------------------------------------------

    pattern = (
        rf"\b{MONTH_PATTERN}\s+"
        rf"(\d{{1,2}})"
        rf"\s*(?:-|–|—|to)\s*"
        rf"(\d{{1,2}})"
        rf"[,]?\s+"
        rf"(20\d{{2}})\b"
    )

    for match in re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    ):
        end_day = int(
            match.group(3)
        )

        add_date(
            int(match.group(4)),
            match.group(1),
            end_day,
        )

    # --------------------------------------------------------
    # 5-10 August 2026
    # 5–10 August 2026
    # 5 to 10 August 2026
    #
    # Use the end date of the range.
    # --------------------------------------------------------

    pattern = (
        rf"\b(\d{{1,2}})"
        rf"\s*(?:-|–|—|to)\s*"
        rf"(\d{{1,2}})\s+"
        rf"{MONTH_PATTERN}\s+"
        rf"(20\d{{2}})\b"
    )

    for match in re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    ):
        end_day = int(
            match.group(2)
        )

        add_date(
            int(match.group(4)),
            match.group(3),
            end_day,
        )

    # --------------------------------------------------------
    # Sep 12
    # September 12
    #
    # Only use when the caller provides a trustworthy
    # fallback year, usually from the opportunity title.
    # --------------------------------------------------------

    if fallback_year is not None:
        pattern = (
            rf"\b{MONTH_PATTERN}\s+"
            rf"(\d{{1,2}})"
            rf"(?:st|nd|rd|th)?\b"
        )

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            add_date(
                fallback_year,
                match.group(1),
                int(match.group(2)),
            )

    # --------------------------------------------------------
    # 12 Sep
    # 12 September
    #
    # Also support day-first date without year when title
    # provides the year.
    # --------------------------------------------------------

    if fallback_year is not None:
        pattern = (
            rf"\b(\d{{1,2}})\s+"
            rf"{MONTH_PATTERN}\b"
        )

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            add_date(
                fallback_year,
                match.group(2),
                int(match.group(1)),
            )

    return found


def classify_lifecycle(
    date_text: str,
    title: str = "",
    today: date | None = None,
) -> tuple[str, str]:
    if today is None:
        today = datetime.now().date()

    lowered = date_text.lower()

    ongoing_markers = [
        "ongoing",
        "recurring",
        "open now",
        "register of interest",
        "applications are ongoing",
    ]

    if any(
        marker in lowered
        for marker in ongoing_markers
    ):
        return (
            "active",
            "Opportunity is marked as ongoing or open.",
        )

    fallback_year = extract_year_from_title(
        title
    )

    explicit_dates = extract_explicit_dates(
        date_text,
        fallback_year=fallback_year,
    )

    if not explicit_dates:
        return (
            "uncertain",
            (
                "No machine-verifiable explicit "
                "date was found."
            ),
        )

    latest_date = max(
        explicit_dates
    )

    if latest_date < today:
        return (
            "expired",
            (
                "Latest explicit date was "
                f"{latest_date.isoformat()}."
            ),
        )

    return (
        "active",
        (
            "Latest explicit date is "
            f"{latest_date.isoformat()}."
        ),
    )


def archive_filename() -> str:
    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S"
    )

    return (
        f"expired_opportunities_{timestamp}.txt"
    )


def main() -> int:
    batch_file = (
        Path(
            sys.argv[1]
        ).resolve()
        if len(sys.argv) >= 2
        else DEFAULT_BATCH_FILE
    )

    if not batch_file.exists():
        print(
            (
                "Lifecycle check failed: "
                "batch file not found: "
                f"{batch_file}"
            )
        )

        return 1

    try:
        text = read_text_with_fallback(
            batch_file
        )

    except Exception as exc:
        print(
            (
                "Lifecycle check failed while "
                f"reading batch: {exc}"
            )
        )

        return 1

    blocks = split_entries(
        text
    )

    if not blocks:
        print(
            (
                "Lifecycle check failed: "
                "no opportunities found."
            )
        )

        return 1

    active: list[
        dict[str, str]
    ] = []

    uncertain: list[
        dict[str, str]
    ] = []

    expired: list[
        dict[str, str]
    ] = []

    details: list[
        dict[str, Any]
    ] = []

    today = datetime.now().date()

    for block in blocks:
        entry = parse_entry(
            block
        )

        title = entry.get(
            "Title",
            "(untitled)",
        )

        date_text = entry.get(
            "Date/Deadline",
            "",
        )

        status, reason = classify_lifecycle(
            date_text,
            title=title,
            today=today,
        )

        details.append(
            {
                "title": title,
                "status": status,
                "reason": reason,
                "date_deadline": date_text,
            }
        )

        if status == "active":
            active.append(
                entry
            )

        elif status == "expired":
            expired.append(
                entry
            )

        else:
            uncertain.append(
                entry
            )

    write_entries(
        ACTIVE_OUTPUT_FILE,
        active,
    )

    write_entries(
        UNCERTAIN_OUTPUT_FILE,
        uncertain,
    )

    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    archive_file = (
        ARCHIVE_DIR
        / archive_filename()
    )

    if expired:
        write_entries(
            archive_file,
            expired,
        )

    else:
        archive_file = None

    STATUS_JSON.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    status = {
        "status": "success",

        "generated_at": (
            datetime.now().isoformat(
                timespec="seconds"
            )
        ),

        "today": today.isoformat(),

        "batch_file": str(
            batch_file
        ),

        "total_entries": len(
            blocks
        ),

        "active": len(
            active
        ),

        "uncertain": len(
            uncertain
        ),

        "expired": len(
            expired
        ),

        "active_file": str(
            ACTIVE_OUTPUT_FILE
        ),

        "uncertain_file": str(
            UNCERTAIN_OUTPUT_FILE
        ),

        "archive_file": (
            str(archive_file)
            if archive_file
            else None
        ),

        "details": details,
    }

    STATUS_JSON.write_text(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    text_status = "\n".join(
        [
            "Lifecycle check completed successfully.",

            (
                "Batch: "
                f"{batch_file}"
            ),

            (
                "Today: "
                f"{today.isoformat()}"
            ),

            (
                "Total Entries: "
                f"{len(blocks)}"
            ),

            (
                "Active: "
                f"{len(active)}"
            ),

            (
                "Uncertain: "
                f"{len(uncertain)}"
            ),

            (
                "Expired: "
                f"{len(expired)}"
            ),

            (
                "Archive File: "
                + (
                    str(archive_file)
                    if archive_file
                    else "none"
                )
            ),
        ]
    )

    STATUS_TXT.write_text(
        text_status,
        encoding="utf-8",
    )

    print(
        text_status
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )