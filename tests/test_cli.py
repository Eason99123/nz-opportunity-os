import subprocess
import sys
from pathlib import Path


def test_cli_help_shows_usage() -> None:
    result = subprocess.run(
        [sys.executable, "src/cli.py", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "python src/cli.py" in result.stdout


def test_cli_missing_input_file_shows_error() -> None:
    result = subprocess.run(
        [sys.executable, "src/cli.py", "input/not_exist.txt"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Input file not found" in result.stdout
    assert "Usage:" in result.stdout


def test_cli_generates_outputs_with_valid_input(tmp_path: Path) -> None:
    input_file = tmp_path / "opportunities.txt"
    json_output = tmp_path / "result.json"
    md_output = tmp_path / "result.md"

    input_file.write_text(
        """Title: Peak Performance & AI - May Meetup
Type: Tech Meetup
Where: Microsoft, Auckland
Date/Deadline: Monday, May 4, 5:30 PM
Why fit: Good networking opportunity and AI-related learning.
Next step: Register on Eventbrite.
Source link: https://example.com/peak
Relevance: 5/5
Beginner Fit: 4/5
Career Value: 4/5
Practicality: 5/5
University Fit: 5/5
Total Score: 23/25
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "src/cli.py", str(input_file), str(json_output), str(md_output)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json_output.exists()
    assert md_output.exists()
    assert "Saved ranked JSON to:" in result.stdout
    assert "Saved markdown summary to:" in result.stdout