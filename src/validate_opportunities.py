from __future__ import annotations

import json
import re
import sys
from datetime import datetime, date
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse, urlunparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INPUT = PROJECT_ROOT / "incoming" / "openclaw_cleaned.txt"

APPROVED_FILE = PROJECT_ROOT / "incoming" / "openclaw_approved.txt"
REVIEW_FILE = PROJECT_ROOT / "incoming" / "openclaw_needs_review.txt"
REJECTED_FILE = PROJECT_ROOT / "incoming" / "openclaw_rejected.txt"

STATUS_JSON = PROJECT_ROOT / "logs" / "latest_validation_status.json"
STATUS_TXT = PROJECT_ROOT / "logs" / "latest_validation_status.txt"


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


SCORE_FIELDS = [
    "Relevance",
    "Beginner Fit",
    "Career Value",
    "Practicality",
    "University Fit",
]


MOJIBAKE_MARKERS = [
    "鈥",
    "鈩",
    "茅",
    "膩",
    "淕",
    "攗",
    "銆",
    "锟",
    "�",
]


SUSPICIOUS_TEXT_PATTERNS = [
    r"\bassum(?:e|ing|ption)\b",
    r"\bthis is tricky\b",
    r"\bneed to pick\b",
    r"\bthe prompt asks\b",
    r"\blet'?s assume\b",
    r"\bspecific dates not detailed\b",
    r"\bcheck website\b",
    r"\bcheck the website\b",
    r"\bTBC\b",
]


MONTH_PATTERN = (
    r"(January|February|March|April|May|June|July|August|"
    r"September|October|November|December|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
)


def read_text_with_fallback(path: Path) -> str:
    encodings = [
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "cp1252",
    ]

    for encoding in encodings:
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
            end = starts[
                index + 1
            ].start()
        else:
            end = len(text)

        block = text[
            start:end
        ].strip()

        if block:
            entries.append(
                block
            )

    return entries


def parse_entry(
    block: str,
) -> dict[str, str]:
    result: dict[str, str] = {}

    current_field = None

    for raw_line in block.splitlines():
        line = raw_line.rstrip()

        matched_field = None

        for field in REQUIRED_FIELDS:
            prefix = f"{field}:"

            if line.startswith(prefix):
                matched_field = field

                value = line[
                    len(prefix):
                ].strip()

                result[field] = value

                current_field = field

                break

        if matched_field:
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

    return "\n".join(
        lines
    )


def normalize_url(
    url: str,
) -> str:
    url = url.strip()

    try:
        parsed = urlparse(
            url
        )

    except ValueError:
        return url.lower()

    scheme = parsed.scheme.lower()

    hostname = (
        parsed.hostname or ""
    ).lower()

    path = parsed.path.rstrip(
        "/"
    )

    cleaned = parsed._replace(
        scheme=scheme,
        netloc=hostname,
        path=path,
        query="",
        fragment="",
    )

    return urlunparse(
        cleaned
    )


def valid_http_url(
    url: str,
) -> bool:
    try:
        parsed = urlparse(
            url
        )

        return (
            parsed.scheme
            in {"http", "https"}
            and bool(
                parsed.netloc
            )
        )

    except ValueError:
        return False


def is_generic_url(
    url: str,
) -> bool:
    try:
        parsed = urlparse(
            url
        )

    except ValueError:
        return False

    hostname = (
        parsed.hostname or ""
    ).lower()

    path = parsed.path.lower()

    query = parsed.query.lower()

    if (
        hostname == "seek.com"
        or hostname.endswith(
            ".seek.com"
        )
        or hostname == "seek.co.nz"
        or hostname.endswith(
            ".seek.co.nz"
        )
    ):
        if "/job/" in path:
            return False

        if (
            "-jobs/" in path
            or "/jobs/" in path
            or "search" in path
            or path.rstrip("/")
            == "/jobs"
            or bool(query)
        ):
            return True

    if (
        hostname == "linkedin.com"
        or hostname.endswith(
            ".linkedin.com"
        )
    ):
        if "/jobs/search" in path:
            return True

    if (
        hostname.startswith(
            "indeed."
        )
        or ".indeed."
        in hostname
    ):
        if (
            "/jobs" in path
            or "/q-" in path
            or "q=" in query
        ):
            return True

    if (
        hostname == "glassdoor.com"
        or hostname.endswith(
            ".glassdoor.com"
        )
    ):
        if (
            "/job-listing"
            in path
            or "/jobs/"
            in path
        ):
            return True

    if "eventbrite." in hostname:
        if path.startswith(
            "/d/"
        ):
            return True

    if (
        hostname == "meetup.com"
        or hostname.endswith(
            ".meetup.com"
        )
    ):
        if path.startswith(
            "/find"
        ):
            return True

    return False


def normalize_text(
    value: str,
) -> str:
    value = value.lower().strip()

    replacements = {
        "&": " and ",
        "–": " ",
        "—": " ",
        "-": " ",
        "|": " ",
        ":": " ",
        "/": " ",
        "\\": " ",
        "(": " ",
        ")": " ",
        ",": " ",
        ".": " ",
    }

    for old, new in replacements.items():
        value = value.replace(
            old,
            new,
        )

    value = re.sub(
        r"\b20\d{2}\b",
        " ",
        value,
    )

    value = re.sub(
        r"\b19\d{2}\b",
        " ",
        value,
    )

    value = re.sub(
        r"\b("
        r"auckland|"
        r"new zealand|"
        r"nz|"
        r"event|"
        r"events|"
        r"programme|"
        r"program"
        r")\b",
        " ",
        value,
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def canonical_title_key(
    title: str,
) -> str:
    return normalize_text(
        title
    )


def title_similarity(
    title_a: str,
    title_b: str,
) -> float:
    a = normalize_text(
        title_a
    )

    b = normalize_text(
        title_b
    )

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


def are_near_duplicate_titles(
    title_a: str,
    title_b: str,
    threshold: float = 0.82,
) -> bool:
    return (
        title_similarity(
            title_a,
            title_b,
        )
        >= threshold
    )


def extract_distinct_event_markers(
    title: str,
) -> set[str]:
    normalized = normalize_text(
        title
    )

    markers: set[str] = set()

    session_match = re.search(
        r"\bsession\s+(\d+)\b",
        normalized,
    )

    if session_match:
        markers.add(
            (
                "session:"
                + session_match.group(1)
            )
        )

    part_match = re.search(
        r"\bpart\s+(\d+)\b",
        normalized,
    )

    if part_match:
        markers.add(
            (
                "part:"
                + part_match.group(1)
            )
        )

    day_match = re.search(
        r"\bday\s+(\d+)\b",
        normalized,
    )

    if day_match:
        markers.add(
            (
                "day:"
                + day_match.group(1)
            )
        )

    keywords = [
        "workshop",
        "prizegiving",
        "grand final",
        "hackathon",
        "meetup",
        "co working",
        "coworking",
        "expo",
        "forum",
        "open day",
        "seminar",
        "webinar",
        "conference",
        "networking",
        "demo",
        "showcase",
    ]

    for keyword in keywords:
        if keyword in normalized:
            markers.add(
                f"type:{keyword}"
            )

    return markers


def clearly_distinct_events(
    title_a: str,
    title_b: str,
) -> bool:
    markers_a = (
        extract_distinct_event_markers(
            title_a
        )
    )

    markers_b = (
        extract_distinct_event_markers(
            title_b
        )
    )

    session_a = {
        marker
        for marker in markers_a
        if marker.startswith(
            "session:"
        )
    }

    session_b = {
        marker
        for marker in markers_b
        if marker.startswith(
            "session:"
        )
    }

    if (
        session_a
        and session_b
        and session_a
        != session_b
    ):
        return True

    part_a = {
        marker
        for marker in markers_a
        if marker.startswith(
            "part:"
        )
    }

    part_b = {
        marker
        for marker in markers_b
        if marker.startswith(
            "part:"
        )
    }

    if (
        part_a
        and part_b
        and part_a
        != part_b
    ):
        return True

    day_a = {
        marker
        for marker in markers_a
        if marker.startswith(
            "day:"
        )
    }

    day_b = {
        marker
        for marker in markers_b
        if marker.startswith(
            "day:"
        )
    }

    if (
        day_a
        and day_b
        and day_a
        != day_b
    ):
        return True

    type_a = {
        marker
        for marker in markers_a
        if marker.startswith(
            "type:"
        )
    }

    type_b = {
        marker
        for marker in markers_b
        if marker.startswith(
            "type:"
        )
    }

    if (
        type_a
        and type_b
        and type_a
        != type_b
    ):
        return True

    return False


def extract_domain(
    url: str,
) -> str:
    try:
        parsed = urlparse(
            url
        )

        return (
            parsed.hostname or ""
        ).lower()

    except ValueError:
        return ""


def contains_mojibake(
    text: str,
) -> bool:
    return any(
        marker in text
        for marker
        in MOJIBAKE_MARKERS
    )


def contains_suspicious_text(
    text: str,
) -> bool:
    for pattern in SUSPICIOUS_TEXT_PATTERNS:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return True

    return False


def parse_score(
    value: str,
) -> int | None:
    match = re.match(
        r"^\s*(\d+)\s*/\s*5\b",
        value,
    )

    if not match:
        return None

    score = int(
        match.group(1)
    )

    if 1 <= score <= 5:
        return score

    return None


def parse_total_score(
    value: str,
) -> int | None:
    match = re.match(
        r"^\s*(\d+)\s*/\s*25\b",
        value,
    )

    if not match:
        return None

    score = int(
        match.group(1)
    )

    if 5 <= score <= 25:
        return score

    return None


def extract_explicit_dates(
    text: str,
) -> list[date]:
    found: list[date] = []

    pattern_day_month_year = (
        rf"\b(\d{{1,2}})\s+"
        rf"{MONTH_PATTERN}\s+"
        rf"(20\d{{2}})\b"
    )

    for match in re.finditer(
        pattern_day_month_year,
        text,
        flags=re.IGNORECASE,
    ):
        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        candidate = (
            f"{day} "
            f"{month} "
            f"{year}"
        )

        for fmt in (
            "%d %B %Y",
            "%d %b %Y",
        ):
            try:
                parsed_date = datetime.strptime(
                    candidate,
                    fmt,
                ).date()

                found.append(
                    parsed_date
                )

                break

            except ValueError:
                pass

    pattern_month_day_year = (
        rf"\b{MONTH_PATTERN}\s+"
        rf"(\d{{1,2}})"
        rf"(?:st|nd|rd|th)?"
        rf"[,]?\s+"
        rf"(20\d{{2}})\b"
    )

    for match in re.finditer(
        pattern_month_day_year,
        text,
        flags=re.IGNORECASE,
    ):
        month = match.group(1)
        day = match.group(2)
        year = match.group(3)

        candidate = (
            f"{month} "
            f"{day} "
            f"{year}"
        )

        for fmt in (
            "%B %d %Y",
            "%b %d %Y",
        ):
            try:
                parsed_date = datetime.strptime(
                    candidate,
                    fmt,
                ).date()

                found.append(
                    parsed_date
                )

                break

            except ValueError:
                pass

    return found


def classify_date(
    date_text: str,
) -> tuple[str, str | None]:
    lowered = date_text.lower()

    if any(
        keyword in lowered
        for keyword in [
            "ongoing",
            "recurring",
            "open now",
            "register of interest",
        ]
    ):
        return (
            "ongoing",
            None,
        )

    explicit_dates = extract_explicit_dates(
        date_text
    )

    if not explicit_dates:
        return (
            "uncertain",
            "No machine-verifiable explicit date",
        )

    latest_date = max(
        explicit_dates
    )

    today = datetime.now().date()

    if latest_date < today:
        return (
            "expired",
            (
                "Latest explicit date was "
                f"{latest_date.isoformat()}"
            ),
        )

    return (
        "future",
        None,
    )


def find_duplicate(
    entry: dict[str, str],
    seen_opportunities: list[dict[str, str]],
) -> tuple[
    bool,
    str | None,
    dict[str, str] | None,
]:
    title = entry.get(
        "Title",
        "",
    ).strip()

    source_url = entry.get(
        "Source link",
        "",
    ).strip()

    normalized_url = normalize_url(
        source_url
    )

    domain = extract_domain(
        source_url
    )

    for previous in seen_opportunities:
        previous_url = previous[
            "normalized_url"
        ]

        previous_title = previous[
            "title"
        ]

        previous_domain = previous[
            "domain"
        ]

        # Exact canonical URL duplicate remains a hard duplicate.
        if (
            normalized_url
            and normalized_url
            == previous_url
        ):
            return (
                True,
                (
                    "Duplicate source URL in "
                    "current validation run"
                ),
                previous,
            )

        similarity = title_similarity(
            title,
            previous_title,
        )

        distinct_events = (
            clearly_distinct_events(
                title,
                previous_title,
            )
        )

        if (
            similarity >= 0.90
            and not distinct_events
        ):
            return (
                True,
                (
                    "Near-duplicate title detected "
                    f"(similarity={similarity:.2f})"
                ),
                previous,
            )

        if (
            domain
            and domain == previous_domain
            and similarity >= 0.82
            and not distinct_events
        ):
            return (
                True,
                (
                    "Likely same opportunity on "
                    "same source domain "
                    f"(similarity={similarity:.2f})"
                ),
                previous,
            )

    return (
        False,
        None,
        None,
    )


def validate_entry(
    entry: dict[str, str],
    seen_opportunities: list[dict[str, str]],
    check_date_status: bool = True,
) -> dict:
    reject_reasons: list[str] = []
    review_reasons: list[str] = []

    missing = [
        field
        for field in REQUIRED_FIELDS
        if not entry.get(
            field,
            "",
        ).strip()
    ]

    if missing:
        reject_reasons.append(
            (
                "Missing required fields: "
                + ", ".join(
                    missing
                )
            )
        )

    source_url = entry.get(
        "Source link",
        "",
    ).strip()

    if source_url:
        if not valid_http_url(
            source_url
        ):
            reject_reasons.append(
                "Invalid source URL"
            )

        elif is_generic_url(
            source_url
        ):
            reject_reasons.append(
                (
                    "Source URL is a generic "
                    "search/listing page"
                )
            )

    duplicate_found = False

    if source_url:
        (
            duplicate_found,
            duplicate_reason,
            duplicate_match,
        ) = find_duplicate(
            entry,
            seen_opportunities,
        )

        if duplicate_found:
            message = (
                duplicate_reason
                or "Duplicate opportunity"
            )

            if duplicate_match:
                message += (
                    "; first seen as: "
                    + duplicate_match[
                        "title"
                    ]
                )

            reject_reasons.append(
                message
            )

    combined_text = " ".join(
        entry.values()
    )

    if contains_mojibake(
        combined_text
    ):
        review_reasons.append(
            (
                "Possible character-encoding "
                "corruption detected"
            )
        )

    if contains_suspicious_text(
        combined_text
    ):
        review_reasons.append(
            (
                "Suspicious commentary or "
                "uncertain wording detected"
            )
        )

    score_values: dict[str, int] = {}

    for field in SCORE_FIELDS:
        value = entry.get(
            field,
            "",
        )

        score = parse_score(
            value
        )

        if score is None:
            reject_reasons.append(
                (
                    f"Invalid score format for "
                    f"{field}: {value!r}"
                )
            )

        else:
            score_values[
                field
            ] = score

    total_value = entry.get(
        "Total Score",
        "",
    )

    declared_total = parse_total_score(
        total_value
    )

    if declared_total is None:
        reject_reasons.append(
            (
                "Invalid Total Score format: "
                f"{total_value!r}"
            )
        )

    elif (
        len(score_values)
        == len(SCORE_FIELDS)
    ):
        calculated_total = sum(
            score_values.values()
        )

        if (
            declared_total
            != calculated_total
        ):
            reject_reasons.append(
                (
                    "Total Score mismatch: "
                    f"declared {declared_total}, "
                    f"calculated {calculated_total}"
                )
            )

    date_status = "not_checked"

    if check_date_status:
        date_text = entry.get(
            "Date/Deadline",
            "",
        )

        (
            date_status,
            date_reason,
        ) = classify_date(
            date_text
        )

        if date_status == "expired":
            reject_reasons.append(
                (
                    "Opportunity appears expired: "
                    f"{date_reason}"
                )
            )

        elif date_status == "uncertain":
            review_reasons.append(
                (
                    date_reason
                    or "Date requires review"
                )
            )

    if reject_reasons:
        status = "rejected"

    elif review_reasons:
        status = "needs_review"

    else:
        status = "approved"

    if not duplicate_found:
        title = entry.get(
            "Title",
            "",
        ).strip()

        normalized_title = (
            canonical_title_key(
                title
            )
        )

        normalized_url = (
            normalize_url(
                source_url
            )
            if source_url
            else ""
        )

        domain = (
            extract_domain(
                source_url
            )
            if source_url
            else ""
        )

        seen_opportunities.append(
            {
                "title": title,
                "normalized_title": normalized_title,
                "normalized_url": normalized_url,
                "domain": domain,
            }
        )

    return {
        "status": status,
        "reject_reasons": reject_reasons,
        "review_reasons": review_reasons,
        "date_status": date_status,
    }


def write_entries(
    path: Path,
    items: list[
        tuple[
            dict[str, str],
            dict,
        ]
    ],
    include_reasons: bool = False,
) -> None:
    blocks = []

    for (
        entry,
        validation,
    ) in items:
        block = serialize_entry(
            entry
        )

        if include_reasons:
            reasons = (
                validation[
                    "reject_reasons"
                ]
                + validation[
                    "review_reasons"
                ]
            )

            if reasons:
                block += (
                    "\nValidation Status: "
                    + validation[
                        "status"
                    ]
                )

                block += (
                    "\nValidation Reasons: "
                    + " | ".join(
                        reasons
                    )
                )

        blocks.append(
            block
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        (
            "\n\n"
            "===OPPORTUNITY==="
            "\n\n"
        ).join(
            blocks
        ),
        encoding="utf-8",
    )


def main() -> int:
    input_file = (
        Path(
            sys.argv[1]
        ).resolve()
        if len(sys.argv) >= 2
        else DEFAULT_INPUT
    )

    if not input_file.exists():
        print(
            (
                "Validation failed: "
                "input file not found: "
                f"{input_file}"
            )
        )

        return 1

    try:
        text = read_text_with_fallback(
            input_file
        )

    except Exception as exc:
        print(
            (
                "Validation failed while "
                f"reading input: {exc}"
            )
        )

        return 1

    raw_entries = split_entries(
        text
    )

    if not raw_entries:
        print(
            (
                "Validation failed: "
                "no opportunity entries found."
            )
        )

        return 1

    approved = []
    review = []
    rejected = []

    seen_opportunities: list[
        dict[str, str]
    ] = []

    for block in raw_entries:
        entry = parse_entry(
            block
        )

        validation = validate_entry(
            entry,
            seen_opportunities,
        )

        item = (
            entry,
            validation,
        )

        if (
            validation[
                "status"
            ]
            == "approved"
        ):
            approved.append(
                item
            )

        elif (
            validation[
                "status"
            ]
            == "needs_review"
        ):
            review.append(
                item
            )

        else:
            rejected.append(
                item
            )

    write_entries(
        APPROVED_FILE,
        approved,
        include_reasons=False,
    )

    write_entries(
        REVIEW_FILE,
        review,
        include_reasons=True,
    )

    write_entries(
        REJECTED_FILE,
        rejected,
        include_reasons=True,
    )

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

        "input_file": str(
            input_file
        ),

        "total_entries": len(
            raw_entries
        ),

        "approved": len(
            approved
        ),

        "needs_review": len(
            review
        ),

        "rejected": len(
            rejected
        ),

        "approved_file": str(
            APPROVED_FILE
        ),

        "needs_review_file": str(
            REVIEW_FILE
        ),

        "rejected_file": str(
            REJECTED_FILE
        ),
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
            "Validation completed successfully.",
            f"Input: {input_file}",
            (
                "Total Entries: "
                f"{len(raw_entries)}"
            ),
            (
                "Approved: "
                f"{len(approved)}"
            ),
            (
                "Needs Review: "
                f"{len(review)}"
            ),
            (
                "Rejected: "
                f"{len(rejected)}"
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