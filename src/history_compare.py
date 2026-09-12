import json
from pathlib import Path
from typing import Any


HISTORY_DIR = Path("opportunities") / "history"
OUTPUT_DIR = Path("opportunities") / "history_changes"
OUTPUT_MD_FILE = OUTPUT_DIR / "latest_changes.md"
OUTPUT_JSON_FILE = OUTPUT_DIR / "latest_changes.json"


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_history_json_files(history_dir: Path) -> list[Path]:
    if not history_dir.exists():
        return []
    return sorted(history_dir.glob("*.json"))


def normalize_title(title: str) -> str:
    return " ".join(title.strip().lower().split())


def build_title_map(opportunities: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in opportunities:
        title = item.get("title")
        if not title:
            continue
        result[normalize_title(title)] = item
    return result


def compare_snapshots(
    older: dict[str, Any],
    newer: dict[str, Any],
    older_file: Path,
    newer_file: Path,
) -> dict[str, Any]:
    old_items = older.get("opportunities", [])
    new_items = newer.get("opportunities", [])

    old_map = build_title_map(old_items)
    new_map = build_title_map(new_items)

    old_titles = set(old_map.keys())
    new_titles = set(new_map.keys())

    added_titles = sorted(new_titles - old_titles)
    removed_titles = sorted(old_titles - new_titles)
    unchanged_titles = sorted(old_titles & new_titles)

    added = [new_map[title] for title in added_titles]
    removed = [old_map[title] for title in removed_titles]

    return {
        "older_snapshot_file": older_file.name,
        "newer_snapshot_file": newer_file.name,
        "older_generated_at": older.get("generated_at", "unknown"),
        "newer_generated_at": newer.get("generated_at", "unknown"),
        "added_count": len(added),
        "removed_count": len(removed),
        "unchanged_count": len(unchanged_titles),
        "added": added,
        "removed": removed,
    }


def format_opportunity_line(item: dict[str, Any]) -> str:
    title = item.get("title", "Untitled")
    score = item.get("total_score", "N/A")
    where = item.get("where", "N/A")
    date_deadline = item.get("date_deadline", "N/A")
    return f"- **{title}** | Score: {score} | Where: {where} | Date/Deadline: {date_deadline}"


def save_markdown_report(report: dict[str, Any], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# History Change Report")
    lines.append("")
    lines.append(f"Older snapshot file: {report['older_snapshot_file']}")
    lines.append(f"Newer snapshot file: {report['newer_snapshot_file']}")
    lines.append(f"Older snapshot time: {report['older_generated_at']}")
    lines.append(f"Newer snapshot time: {report['newer_generated_at']}")
    lines.append("")

    lines.append("## New Opportunities")
    lines.append("")
    if report["added"]:
      for item in report["added"]:
          lines.append(format_opportunity_line(item))
    else:
        lines.append("None")
    lines.append("")

    lines.append("## Removed Opportunities")
    lines.append("")
    if report["removed"]:
        for item in report["removed"]:
            lines.append(format_opportunity_line(item))
    else:
        lines.append("None")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Added count: {report['added_count']}")
    lines.append(f"- Removed count: {report['removed_count']}")
    lines.append(f"- Unchanged count: {report['unchanged_count']}")
    lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")


def save_json_report(report: dict[str, Any], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def main() -> None:
    history_files = get_history_json_files(HISTORY_DIR)

    if len(history_files) < 2:
        print("Need at least two history JSON files to compare.")
        return

    older_file = history_files[-2]
    newer_file = history_files[-1]

    older_payload = load_json_file(older_file)
    newer_payload = load_json_file(newer_file)

    report = compare_snapshots(older_payload, newer_payload, older_file, newer_file)

    save_markdown_report(report, OUTPUT_MD_FILE)
    save_json_report(report, OUTPUT_JSON_FILE)

    print(f"Compared:\n- {older_file.name}\n- {newer_file.name}")
    print(f"Saved markdown report to: {OUTPUT_MD_FILE.resolve()}")
    print(f"Saved JSON report to: {OUTPUT_JSON_FILE.resolve()}")


if __name__ == "__main__":
    main()