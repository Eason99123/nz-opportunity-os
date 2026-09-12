import re
from typing import Any


def parse_score(value: str) -> int | None:
    match = re.search(r"\d+", value)
    if match:
        return int(match.group())
    return None


def normalize_key(key: str) -> str:
    key = key.strip().lower()
    key = key.replace("/", "_")
    key = key.replace(" ", "_")
    key = key.replace("-", "_")
    return key


def normalize_title(title: str) -> str:
    title = title.strip().lower()
    title = re.sub(r"\s+", " ", title)
    return title


def parse_opportunity_block(block: str) -> dict[str, Any]:
    data: dict[str, Any] = {}

    key_map = {
        "title": "title",
        "type": "type",
        "where": "where",
        "date_deadline": "date_deadline",
        "why_fit": "why_fit",
        "next_step": "next_step",
        "source_link": "source_link",
        "relevance": "relevance",
        "beginner_fit": "beginner_fit",
        "career_value": "career_value",
        "practicality": "practicality",
        "university_fit": "university_fit",
        "total_score": "total_score",
    }

    score_fields = {
        "relevance",
        "beginner_fit",
        "career_value",
        "practicality",
        "university_fit",
        "total_score",
    }

    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue

        raw_key, raw_value = line.split(":", 1)
        key = normalize_key(raw_key)
        value = raw_value.strip()

        if key not in key_map:
            continue

        final_key = key_map[key]

        if final_key in score_fields:
            data[final_key] = parse_score(value)
        else:
            data[final_key] = value

    return data


def split_blocks(text: str) -> list[str]:
    parts = re.split(r"(?=^Title:)", text, flags=re.MULTILINE)
    return [part.strip() for part in parts if part.strip()]


def parse_opportunities(text: str) -> list[dict[str, Any]]:
    blocks = split_blocks(text)
    opportunities = [parse_opportunity_block(block) for block in blocks]
    return [item for item in opportunities if item]

def parse_opportunities_file(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    return parse_opportunities(text)