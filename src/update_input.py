from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
INPUT_FILE = INPUT_DIR / "opportunities.txt"
ARCHIVE_DIR = INPUT_DIR / "archive"


USAGE = """
Usage:
    python src/update_input.py <raw_text_file>

Example:
    python src/update_input.py incoming/new_opportunities.txt
""".strip()


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Source file is empty.")
    return text


def archive_input_copy(source_file: Path, new_text: str) -> tuple[Path, Path]:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    archived_raw_file = ARCHIVE_DIR / f"{timestamp}_raw.txt"
    archived_input_file = ARCHIVE_DIR / f"{timestamp}_input.txt"

    shutil.copy2(source_file, archived_raw_file)
    archived_input_file.write_text(new_text, encoding="utf-8")

    return archived_raw_file, archived_input_file


def overwrite_main_input(new_text: str) -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_FILE.write_text(new_text + "\n", encoding="utf-8")


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


def main() -> None:
    args = sys.argv[1:]

    if any(arg in {"-h", "--help"} for arg in args):
        print(USAGE)
        sys.exit(0)

    if len(args) != 1:
        print("Error: expected exactly one source file.\n")
        print(USAGE)
        sys.exit(1)

    source_file = Path(args[0])
    if not source_file.is_absolute():
        source_file = (PROJECT_ROOT / source_file).resolve()

    try:
        new_text = read_text_file(source_file)

        archived_raw_file, archived_input_file = archive_input_copy(source_file, new_text)
        overwrite_main_input(new_text)

        print(f"Updated main input file: {INPUT_FILE}")
        print(f"Archived raw source to: {archived_raw_file}")
        print(f"Archived normalized input copy to: {archived_input_file}")
        print()

        run_command([sys.executable, "src/cli.py"])
        print()
        run_command([sys.executable, "src/history_compare.py"])
        print()
        print("Input refresh pipeline completed successfully.")

    except Exception as error:
        print(f"Update failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()