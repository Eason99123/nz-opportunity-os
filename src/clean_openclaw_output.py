from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"

USAGE = """
Usage:
    python src/clean_openclaw_output.py <raw_input_file> [cleaned_output_file]

Examples:
    python src/clean_openclaw_output.py incoming/openclaw_raw.txt
    python src/clean_openclaw_output.py incoming/openclaw_raw.txt incoming/openclaw_cleaned.txt
""".strip()

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

REQUIRED_FIELDS = FIELD_ORDER[:]


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Raw input file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Raw input file is empty.")
    return text


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_line(line: str) -> str:
    text = line.strip()
    text = text.replace("\u2022", "")
    text = re.sub(r"^\d+\.\s*", "", text)
    text = re.sub(r"^\-\s*", "", text)
    return text.strip()


def is_truncated_line(line: str) -> bool:
    lowered = line.lower()
    return "truncated" in lowered or lowered == "..." or lowered == "(truncated)"


def extract_field_name(line: str) -> str | None:
    for field in FIELD_ORDER:
        prefix = f"{field}:"
        if line.startswith(prefix):
            return field
    return None


def has_required_fields(entry: dict[str, str]) -> bool:
    return all(entry.get(field, "").strip() for field in REQUIRED_FIELDS)


def parse_raw_openclaw_text(raw_text: str) -> list[dict[str, str]]:
    lines = [normalize_line(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line]

    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}

    for line in lines:
        if is_truncated_line(line):
            current = {}
            continue

        field_name = extract_field_name(line)
        if field_name is None:
            continue

        value = line.split(":", 1)[1].strip()

        if field_name == "Title" and current:
            if has_required_fields(current):
                entries.append(current)
            current = {}

        current[field_name] = value

    if current and has_required_fields(current):
        entries.append(current)

    return entries


def render_entries(entries: list[dict[str, str]]) -> str:
    blocks: list[str] = []

    for entry in entries:
        lines: list[str] = []
        for field in FIELD_ORDER:
            lines.append(f"{field}: {entry[field]}")
        blocks.append("\n".join(lines))

    if not blocks:
        return ""

    return "\n\n".join(blocks) + "\n"


def main() -> None:
    args = sys.argv[1:]

    if any(arg in {"-h", "--help"} for arg in args):
        print(USAGE)
        sys.exit(0)

    if len(args) not in {1, 2}:
        print("Error: expected 1 or 2 arguments.\n")
        print(USAGE)
        sys.exit(1)

    raw_input = Path(args[0])
    if not raw_input.is_absolute():
        raw_input = (PROJECT_ROOT / raw_input).resolve()

    if len(args) == 2:
        cleaned_output = Path(args[1])
        if not cleaned_output.is_absolute():
            cleaned_output = (PROJECT_ROOT / cleaned_output).resolve()
    else:
        cleaned_output = INCOMING_DIR / "openclaw_cleaned.txt"

    try:
        raw_text = read_text_file(raw_input)
        entries = parse_raw_openclaw_text(raw_text)

        if not entries:
            raise ValueError(
                "No complete opportunity entries were found. "
                "The raw output may be truncated or missing required fields."
            )

        cleaned_text = render_entries(entries)
        write_text_file(cleaned_output, cleaned_text)

        print(f"Raw input file: {raw_input}")
        print(f"Cleaned output file: {cleaned_output}")
        print(f"Valid opportunities found: {len(entries)}")
        print()
        print("Cleaning completed successfully.")

    except Exception as error:
        print(f"Cleaning failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()