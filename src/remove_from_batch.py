from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_FILE = PROJECT_ROOT / "incoming" / "openclaw_batch.txt"
WRITE_BATCH_STATUS = PROJECT_ROOT / "src" / "write_batch_status.py"

FIELD_ORDER = [
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

USAGE = """
Usage:
    python src/remove_from_batch.py "<title keyword>"

Example:
    python src/remove_from_batch.py "Physical AI Meetup"
""".strip()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def parse_entries(text: str) -> list[dict[str, str]]:
    blocks = [block.strip() for block in text.strip().split("\n\n") if block.strip()]
    entries: list[dict[str, str]] = []

    for block in blocks:
        entry: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            field, value = line.split(":", 1)
            field = field.strip()
            value = value.strip()
            if field in FIELD_ORDER:
                entry[field] = value

        if all(field in entry and entry[field] for field in FIELD_ORDER):
            entries.append(entry)

    return entries


def render_entries(entries: list[dict[str, str]]) -> str:
    if not entries:
        return ""

    blocks: list[str] = []
    for entry in entries:
        lines = [f"{field}: {entry[field]}" for field in FIELD_ORDER]
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks) + "\n"


def main() -> None:
    args = sys.argv[1:]

    if any(arg in {"-h", "--help"} for arg in args):
        print(USAGE)
        sys.exit(0)

    if len(args) != 1:
        print("Error: expected exactly one title keyword.\n")
        print(USAGE)
        sys.exit(1)

    if not BATCH_FILE.exists():
        print(f"Remove failed: batch file not found: {BATCH_FILE}")
        sys.exit(1)

    keyword = normalize_text(args[0])
    if not keyword:
        print("Remove failed: empty title keyword.")
        sys.exit(1)

    text = BATCH_FILE.read_text(encoding="utf-8").strip()
    entries = parse_entries(text) if text else []

    if not entries:
        print("Remove failed: batch file is empty.")
        sys.exit(1)

    kept_entries: list[dict[str, str]] = []
    removed_titles: list[str] = []

    for entry in entries:
        title = entry["Title"]
        if keyword in normalize_text(title):
            removed_titles.append(title)
        else:
            kept_entries.append(entry)

    if not removed_titles:
        print(f'No batch entries matched: "{args[0]}"')
        sys.exit(0)

    BATCH_FILE.write_text(render_entries(kept_entries), encoding="utf-8")

    print(f'Keyword: "{args[0]}"')
    print(f"Removed entries: {len(removed_titles)}")
    for title in removed_titles:
        print(f"- {title}")
    print(f"Remaining batch entries: {len(kept_entries)}")
    print()
    print("Batch removal completed successfully.")


if __name__ == "__main__":
    main()