import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "src"
    ),
)

from verification_cli import (
    get_opportunities_needing_verification,
    load_payload,
    save_payload,
)


def make_opportunity(
    title: str,
    status: str,
) -> dict:
    return {
        "title": title,
        "total_score": 20,
        "source_link": "https://example.com",
        "verification": {
            "application_status": status,
        },
    }


def test_get_opportunities_needing_verification():
    opportunities = [
        make_opportunity(
            "Opportunity A",
            "OPEN_UNVERIFIED",
        ),
        make_opportunity(
            "Opportunity B",
            "OPEN_VERIFIED",
        ),
        make_opportunity(
            "Opportunity C",
            "CLOSED",
        ),
    ]

    result = (
        get_opportunities_needing_verification(
            opportunities
        )
    )

    assert len(result) == 1
    assert result[0]["title"] == "Opportunity A"


def test_missing_verification_defaults_to_unverified():
    opportunity = {
        "title": "New Opportunity",
        "total_score": 10,
    }

    result = (
        get_opportunities_needing_verification(
            [opportunity]
        )
    )

    assert len(result) == 1
    assert result[0]["title"] == "New Opportunity"


def test_no_pending_opportunities():
    opportunities = [
        make_opportunity(
            "Verified Opportunity",
            "OPEN_VERIFIED",
        ),
        make_opportunity(
            "Closed Opportunity",
            "CLOSED",
        ),
    ]

    result = (
        get_opportunities_needing_verification(
            opportunities
        )
    )

    assert result == []


def test_save_and_load_payload(
    tmp_path: Path,
):
    output_file = (
        tmp_path / "opportunities.json"
    )

    payload = {
        "opportunities": [
            make_opportunity(
                "Test Opportunity",
                "OPEN_UNVERIFIED",
            )
        ]
    }

    save_payload(
        payload,
        output_file,
    )

    loaded = load_payload(
        output_file
    )

    assert loaded == payload


def test_save_payload_creates_parent_directory(
    tmp_path: Path,
):
    output_file = (
        tmp_path
        / "nested"
        / "folder"
        / "opportunities.json"
    )

    payload = {
        "opportunities": []
    }

    save_payload(
        payload,
        output_file,
    )

    assert output_file.exists()


def test_load_payload_missing_file(
    tmp_path: Path,
):
    missing_file = (
        tmp_path / "missing.json"
    )

    try:
        load_payload(
            missing_file
        )
    except FileNotFoundError:
        pass
    else:
        raise AssertionError(
            "Expected FileNotFoundError"
        )


def test_saved_json_is_valid(
    tmp_path: Path,
):
    output_file = (
        tmp_path / "output.json"
    )

    payload = {
        "opportunities": [],
        "count": 0,
    }

    save_payload(
        payload,
        output_file,
    )

    with output_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw = json.load(file)

    assert raw["count"] == 0
    assert raw["opportunities"] == []