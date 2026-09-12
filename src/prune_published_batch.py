from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_FILE = PROJECT_ROOT / "incoming" / "openclaw_batch.txt"
LIVE_JSON_FILE = PROJECT_ROOT / "opportunities" / "deduplicated_ranked_output.json"

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
    python src/prune_published_batch.py
""".strip()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def parse_batch_entries(text: str) -> list[dict[str, str]]:
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


def render_batch_entries(entries: list[dict[str, str]]) -> str:
    if not entries:
        return ""

    blocks: list[str] = []
    for entry in entries:
        lines = [f"{field}: {entry[field]}" for field in FIELD_ORDER]
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks) + "\n"


def read_live_published_titles() -> set[str]:
    if not LIVE_JSON_FILE.exists():
        raise FileNotFoundError(f"Live JSON file not found: {LIVE_JSON_FILE}")

    payload = json.loads(LIVE_JSON_FILE.read_text(encoding="utf-8"))
    opportunities = payload.get("opportunities", [])

    published_titles = {
        normalize_text(item.get("title", ""))
        for item in opportunities
        if normalize_text(item.get("title", ""))
    }
    return published_titles


def main() -> None:
    args = sys.argv[1:]

    if any(arg in {"-h", "--help"} for arg in args):
        print(USAGE)
        sys.exit(0)

    if args:
        print("Error: this script does not take any arguments.\n")
        print(USAGE)
        sys.exit(1)

    if not BATCH_FILE.exists():
        print(f"Prune failed: batch file not found: {BATCH_FILE}")
        sys.exit(1)

    batch_text = BATCH_FILE.read_text(encoding="utf-8").strip()
    batch_entries = parse_batch_entries(batch_text) if batch_text else []

    if not batch_entries:
        print("Prune finished: batch file is already empty.")
        sys.exit(0)

    published_titles = read_live_published_titles()

    kept_entries: list[dict[str, str]] = []
    removed_titles: list[str] = []

    for entry in batch_entries:
        title = entry["Title"]
        title_key = normalize_text(title)

        if title_key in published_titles:
            removed_titles.append(title)
        else:
            kept_entries.append(entry)

    BATCH_FILE.write_text(render_batch_entries(kept_entries), encoding="utf-8")

    print(f"Original batch entries: {len(batch_entries)}")
    print(f"Removed published entries: {len(removed_titles)}")
    if removed_titles:
        for title in removed_titles:
            print(f"- {title}")
    print(f"Remaining batch entries: {len(kept_entries)}")
    print()
    print("Batch prune completed successfully.")


if __name__ == "__main__":
    main()