from __future__ import annotations

import json
import re
import sys
from datetime import datetime, UTC
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"
LOGS_DIR = PROJECT_ROOT / "logs"

BATCH_FILE = INCOMING_DIR / "openclaw_batch.txt"
CLEANED_FILE = INCOMING_DIR / "openclaw_cleaned.txt"

LATEST_APPEND_STATUS_JSON = LOGS_DIR / "latest_append_status.json"
LATEST_APPEND_STATUS_TXT = LOGS_DIR / "latest_append_status.txt"

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


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def parse_score(score_text: str) -> int:
    match = re.search(r"(\d+)", str(score_text))
    return int(match.group(1)) if match else -1


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
    blocks: list[str] = []

    for entry in entries:
        lines = [f"{field}: {entry[field]}" for field in FIELD_ORDER]
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks).strip() + ("\n" if blocks else "")


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def write_append_status_files(payload: dict[str, object]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "OpenClaw Batch Append Status",
        "",
        f"Status: {payload['status']}",
        f"Message: {payload['message']}",
        f"Generated at: {payload['generated_at']}",
        f"Source cleaned file: {payload['source_cleaned_file']}",
        f"Batch file: {payload['batch_file']}",
        "",
        f"New valid entries read: {payload['new_valid_entries_read']}",
        f"New unique entries appended: {payload['new_unique_entries_appended']}",
        f"Replaced existing entries: {payload['replaced_existing_entries']}",
        f"Skipped duplicate entries: {payload['skipped_duplicate_entries']}",
        f"Total batch entries: {payload['total_batch_entries']}",
        "",
    ]

    replacements = payload.get("replacements", [])
    if isinstance(replacements, list) and replacements:
        lines.append("Replacements:")
        for item in replacements:
            if isinstance(item, dict):
                lines.append(f'- Title: "{item.get("title", "")}"')
                lines.append(
                    f'  Replaced because new score is higher: {item.get("old_score", "N/A")} -> {item.get("new_score", "N/A")}'
                )
        lines.append("")

    skipped = payload.get("skipped_duplicates", [])
    if isinstance(skipped, list) and skipped:
        lines.append("Skipped duplicates:")
        for item in skipped:
            if isinstance(item, dict):
                lines.append(f'- Incoming title: "{item.get("incoming_title", "")}"')
                lines.append(f'  Matched existing title: "{item.get("matched_existing_title", "")}"')
                lines.append(f'  Existing score: {item.get("existing_score", "N/A")}')
                lines.append(f'  Incoming score: {item.get("incoming_score", "N/A")}')
        lines.append("")

    LATEST_APPEND_STATUS_TXT.write_text("\n".join(lines), encoding="utf-8")
    LATEST_APPEND_STATUS_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    generated_at = datetime.now(UTC).isoformat()

    try:
        cleaned_text = read_text(CLEANED_FILE)
        new_entries = parse_entries(cleaned_text)

        if not new_entries:
            raise ValueError("No valid entries found in incoming/openclaw_cleaned.txt")

        existing_entries: list[dict[str, str]] = []
        if BATCH_FILE.exists():
            existing_text = BATCH_FILE.read_text(encoding="utf-8").strip()
            if existing_text:
                existing_entries = parse_entries(existing_text)

        existing_index_map = {
            normalize_title(entry["Title"]): idx
            for idx, entry in enumerate(existing_entries)
        }

        added_count = 0
        skipped_duplicates: list[dict[str, object]] = []
        replaced_entries: list[dict[str, object]] = []

        for entry in new_entries:
            new_title = entry["Title"]
            new_score = parse_score(entry["Total Score"])
            title_key = normalize_title(new_title)

            if title_key not in existing_index_map:
                existing_entries.append(entry)
                existing_index_map[title_key] = len(existing_entries) - 1
                added_count += 1
                continue

            existing_idx = existing_index_map[title_key]
            existing_entry = existing_entries[existing_idx]
            existing_title = existing_entry["Title"]
            existing_score = parse_score(existing_entry["Total Score"])

            if new_score > existing_score:
                existing_entries[existing_idx] = entry
                replaced_entries.append(
                    {
                        "title": new_title,
                        "old_score": existing_score,
                        "new_score": new_score,
                    }
                )
            else:
                skipped_duplicates.append(
                    {
                        "incoming_title": new_title,
                        "matched_existing_title": existing_title,
                        "existing_score": existing_score,
                        "incoming_score": new_score,
                    }
                )

        BATCH_FILE.write_text(render_entries(existing_entries), encoding="utf-8")

        payload: dict[str, object] = {
            "status": "success",
            "message": "Batch append completed successfully.",
            "generated_at": generated_at,
            "source_cleaned_file": str(CLEANED_FILE),
            "batch_file": str(BATCH_FILE),
            "new_valid_entries_read": len(new_entries),
            "new_unique_entries_appended": added_count,
            "replaced_existing_entries": len(replaced_entries),
            "skipped_duplicate_entries": len(skipped_duplicates),
            "total_batch_entries": len(existing_entries),
            "replacements": replaced_entries,
            "skipped_duplicates": skipped_duplicates,
        }
        write_append_status_files(payload)

        print(f"Source cleaned file: {CLEANED_FILE}")
        print(f"Batch file: {BATCH_FILE}")
        print(f"New valid entries read: {len(new_entries)}")
        print(f"New unique entries appended: {added_count}")
        print(f"Replaced existing entries: {len(replaced_entries)}")
        print(f"Skipped duplicate entries: {len(skipped_duplicates)}")
        print(f"Total batch entries: {len(existing_entries)}")
        print()

        if replaced_entries:
            print("Replacements:")
            for item in replaced_entries:
                print(f'- Title: "{item["title"]}"')
                print(f'  Replaced because new score is higher: {item["old_score"]} -> {item["new_score"]}')
            print()

        if skipped_duplicates:
            print("Skipped duplicates:")
            for item in skipped_duplicates:
                print(f'- Incoming title: "{item["incoming_title"]}"')
                print(f'  Matched existing title: "{item["matched_existing_title"]}"')
                print(f'  Existing score: {item["existing_score"]}')
                print(f'  Incoming score: {item["incoming_score"]}')
            print()

        print(f"Wrote append status JSON: {LATEST_APPEND_STATUS_JSON}")
        print(f"Wrote append status text: {LATEST_APPEND_STATUS_TXT}")
        print()
        print("Batch append completed successfully.")

    except Exception as error:
        payload = {
            "status": "failed",
            "message": str(error),
            "generated_at": generated_at,
            "source_cleaned_file": str(CLEANED_FILE),
            "batch_file": str(BATCH_FILE),
            "new_valid_entries_read": 0,
            "new_unique_entries_appended": 0,
            "replaced_existing_entries": 0,
            "skipped_duplicate_entries": 0,
            "total_batch_entries": 0,
            "replacements": [],
            "skipped_duplicates": [],
        }
        write_append_status_files(payload)
        print(f"Batch append failed: {error}")
        print(f"Wrote append status JSON: {LATEST_APPEND_STATUS_JSON}")
        print(f"Wrote append status text: {LATEST_APPEND_STATUS_TXT}")
        sys.exit(1)


if __name__ == "__main__":
    main()