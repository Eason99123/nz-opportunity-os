from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"
BATCH_FILE = INCOMING_DIR / "openclaw_batch.txt"
LOGS_DIR = PROJECT_ROOT / "logs"
BATCH_STATUS_JSON = LOGS_DIR / "latest_batch_status.json"
BATCH_STATUS_TXT = LOGS_DIR / "latest_batch_status.txt"

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


def build_preview_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    preview_entries: list[dict[str, str]] = []

    for entry in entries:
        preview_entries.append(
            {
                "title": entry["Title"],
                "type": entry["Type"],
                "where": entry["Where"],
                "date_deadline": entry["Date/Deadline"],
                "total_score": entry["Total Score"],
                "source_link": entry["Source link"],
            }
        )

    return preview_entries


def build_payload() -> dict[str, object]:
    exists = BATCH_FILE.exists()
    entry_count = 0
    updated_at = "unavailable"
    titles: list[str] = []
    preview_entries: list[dict[str, str]] = []
    full_entries: list[dict[str, str]] = []

    if exists:
        text = BATCH_FILE.read_text(encoding="utf-8").strip()
        if text:
            entries = parse_entries(text)
            entry_count = len(entries)
            titles = [entry["Title"] for entry in entries]
            preview_entries = build_preview_entries(entries)
            full_entries = entries
        updated_at = datetime.fromtimestamp(BATCH_FILE.stat().st_mtime, UTC).isoformat()

    return {
        "batch_file": str(BATCH_FILE),
        "exists": "yes" if exists else "no",
        "entry_count": entry_count,
        "titles": titles,
        "preview_entries": preview_entries,
        "full_entries": full_entries,
        "updated_at": updated_at,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def write_status_files(payload: dict[str, object]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    title_lines = payload["titles"] if isinstance(payload["titles"], list) else []

    lines = [
        "OpenClaw Batch Status",
        "",
        f"Batch file: {payload['batch_file']}",
        f"Exists: {payload['exists']}",
        f"Entry count: {payload['entry_count']}",
        f"Updated at: {payload['updated_at']}",
        f"Generated at: {payload['generated_at']}",
        "",
        "Titles:",
    ]

    if title_lines:
        for title in title_lines:
            lines.append(f"- {title}")
    else:
        lines.append("None")

    lines.append("")

    BATCH_STATUS_TXT.write_text("\n".join(lines), encoding="utf-8")
    BATCH_STATUS_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    payload = build_payload()
    write_status_files(payload)
    print(f"Wrote batch status JSON: {BATCH_STATUS_JSON}")
    print(f"Wrote batch status text: {BATCH_STATUS_TXT}")


if __name__ == "__main__":
    main()