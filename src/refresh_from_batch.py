from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_FILE = PROJECT_ROOT / "incoming" / "openclaw_batch.txt"

LOGS_DIR = PROJECT_ROOT / "logs"
LATEST_STATUS_TXT = LOGS_DIR / "latest_refresh_status.txt"
LATEST_STATUS_JSON = LOGS_DIR / "latest_refresh_status.json"
LATEST_BATCH_LOG = LOGS_DIR / "latest_batch_refresh.log"

MAIN_JSON_OUTPUT = PROJECT_ROOT / "opportunities" / "deduplicated_ranked_output.json"
MAIN_MD_OUTPUT = PROJECT_ROOT / "opportunities" / "weekly_summary.md"
MAIN_CSV_OUTPUT = PROJECT_ROOT / "opportunities" / "opportunities.csv"
HISTORY_DIR = PROJECT_ROOT / "opportunities" / "history"
HISTORY_CHANGES_DIR = PROJECT_ROOT / "opportunities" / "history_changes"

USAGE = """
Usage:
    python src/refresh_from_batch.py

This command:
1. Reads incoming/openclaw_batch.txt
2. Updates input/opportunities.txt
3. Rebuilds ranked outputs and history reports
4. Updates logs/latest_refresh_status.txt and logs/latest_refresh_status.json
""".strip()


def run_command(args: list[str]) -> None:
    result = subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )

    print(f"$ {' '.join(args)}")
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {' '.join(args)}"
        )


def get_latest_file_name(directory: Path, pattern: str) -> str:
    if not directory.exists():
        return "unavailable"

    matches = sorted(directory.glob(pattern))
    if not matches:
        return "unavailable"

    return matches[-1].name


def build_status_payload(
    status: str,
    message: str,
    started_at: datetime,
    finished_at: datetime,
) -> dict[str, str]:
    return {
        "status": status,
        "message": message,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "raw_input_file": str(BATCH_FILE),
        "cleaned_output_file": str(BATCH_FILE),
        "main_json_output": str(MAIN_JSON_OUTPUT),
        "main_csv_output": str(MAIN_CSV_OUTPUT),
        "main_markdown_output": str(MAIN_MD_OUTPUT),
        "latest_history_json": get_latest_file_name(HISTORY_DIR, "*.json"),
        "latest_history_csv": get_latest_file_name(HISTORY_DIR, "*.csv"),
        "latest_history_md": get_latest_file_name(HISTORY_DIR, "*.md"),
        "latest_changes_json": get_latest_file_name(HISTORY_CHANGES_DIR, "*.json"),
        "latest_changes_md": get_latest_file_name(HISTORY_CHANGES_DIR, "*.md"),
        "latest_run_log": LATEST_BATCH_LOG.name,
    }


def write_status_files(payload: dict[str, str]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "OpenClaw Refresh Status",
        "",
        f"Status: {payload['status']}",
        f"Message: {payload['message']}",
        f"Started at: {payload['started_at']}",
        f"Finished at: {payload['finished_at']}",
        "",
        f"Raw input file: {payload['raw_input_file']}",
        f"Cleaned output file: {payload['cleaned_output_file']}",
        "",
        f"Main JSON output: {payload['main_json_output']}",
        f"Main CSV output: {payload['main_csv_output']}",
        f"Main Markdown output: {payload['main_markdown_output']}",
        "",
        f"Latest history JSON: {payload['latest_history_json']}",
        f"Latest history CSV: {payload['latest_history_csv']}",
        f"Latest history Markdown: {payload['latest_history_md']}",
        "",
        f"Latest changes JSON: {payload['latest_changes_json']}",
        f"Latest changes Markdown: {payload['latest_changes_md']}",
        f"Latest run log: {payload['latest_run_log']}",
        "",
    ]

    LATEST_STATUS_TXT.write_text("\n".join(lines), encoding="utf-8")
    LATEST_STATUS_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    args = sys.argv[1:]

    if any(arg in {"-h", "--help"} for arg in args):
        print(USAGE)
        sys.exit(0)

    if args:
        print("Error: this script does not take any arguments.\n")
        print(USAGE)
        sys.exit(1)

    started_at = datetime.now(UTC)

    if not BATCH_FILE.exists():
        finished_at = datetime.now(UTC)
        payload = build_status_payload(
            status="failed",
            message=f"Batch file not found: {BATCH_FILE}",
            started_at=started_at,
            finished_at=finished_at,
        )
        write_status_files(payload)
        print(f"Refresh failed: batch file not found: {BATCH_FILE}")
        sys.exit(1)

    try:
        run_command(
            [
                sys.executable,
                "src/update_input.py",
                str(BATCH_FILE),
            ]
        )
        print()

        finished_at = datetime.now(UTC)
        payload = build_status_payload(
            status="success",
            message="Batch refresh pipeline completed successfully.",
            started_at=started_at,
            finished_at=finished_at,
        )
        write_status_files(payload)

        print("Batch refresh pipeline completed successfully.")
        print(f"Latest status text: {LATEST_STATUS_TXT}")
        print(f"Latest status JSON: {LATEST_STATUS_JSON}")

    except Exception as error:
        finished_at = datetime.now(UTC)
        payload = build_status_payload(
            status="failed",
            message=str(error),
            started_at=started_at,
            finished_at=finished_at,
        )
        write_status_files(payload)

        print(f"Batch refresh failed: {error}")
        print(f"Latest status text: {LATEST_STATUS_TXT}")
        print(f"Latest status JSON: {LATEST_STATUS_JSON}")
        sys.exit(1)


if __name__ == "__main__":
    main()