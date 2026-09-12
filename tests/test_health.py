from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)


from write_automation_health import (
    parse_datetime,
    status_is_success,
)


def test_success_status_is_healthy_component():
    data = {
        "status": "success"
    }

    assert status_is_success(
        data
    ) is True


def test_failed_status_is_not_healthy_component():
    data = {
        "status": "failed"
    }

    assert status_is_success(
        data
    ) is False


def test_missing_status_is_not_success():
    assert status_is_success(
        None
    ) is False


def test_iso_timestamp_can_be_parsed():
    result = parse_datetime(
        "2026-09-08T11:33:18"
    )

    assert result is not None
    assert result.year == 2026
    assert result.month == 9
    assert result.day == 8


def test_space_timestamp_can_be_parsed():
    result = parse_datetime(
        "2026-09-08 11:33:18"
    )

    assert result is not None