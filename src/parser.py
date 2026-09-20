import re
from typing import Any


# ============================================================
# Score parsing
# ============================================================

def parse_score(value: str) -> int | None:
    """
    Extract the first integer from a score field.

    Examples:
        "5" -> 5
        "5/5" -> 5
        "Score: 4" -> 4
    """

    match = re.search(r"\d+", value)

    if match:
        return int(match.group())

    return None


# ============================================================
# Key normalisation
# ============================================================

def normalize_key(key: str) -> str:
    """
    Normalise field names produced by OpenClaw.

    Handles common punctuation variants and converts them
    into a consistent lowercase form.
    """

    key = key.strip().lower()

    key = key.replace("–", "-")
    key = key.replace("—", "-")
    key = key.replace(" ", "_")

    return key


# ============================================================
# Title normalisation
# ============================================================

def normalize_title(title: str) -> str:
    """
    Normalise opportunity titles for duplicate detection.
    """

    title = title.strip().lower()
    title = re.sub(r"\s+", " ", title)

    return title


# ============================================================
# Opportunity block parser
# ============================================================

def parse_opportunity_block(
    block: str,
) -> dict[str, Any]:
    """
    Parse one OpenClaw opportunity block into a dictionary.

    Existing fields remain fully supported.

    v1.1 adds:
        company
        source_type

    These fields are optional so older opportunity data remains
    compatible with the parser.
    """

    data: dict[str, Any] = {}

    key_map = {
        "title": "title",
        "company": "company",
        "type": "type",
        "where": "where",
        "date_deadline": "date_deadline",
        "why_fit": "why_fit",
        "next_step": "next_step",
        "source_link": "source_link",
        "source_type": "source_type",
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


# ============================================================
# Block splitting
# ============================================================

def split_blocks(text: str) -> list[str]:
    """
    Split an OpenClaw response into individual opportunity
    blocks.

    Each block begins with:

        Title:
    """

    parts = re.split(
        r"(?=Title:)",
        text,
        flags=re.MULTILINE,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


# ============================================================
# Parse opportunities from text
# ============================================================

def parse_opportunities(
    text: str,
) -> list[dict[str, Any]]:
    """
    Parse all opportunity blocks from a text response.
    """

    blocks = split_blocks(text)

    opportunities = [
        parse_opportunity_block(block)
        for block in blocks
    ]

    return [
        item
        for item in opportunities
        if item
    ]


# ============================================================
# Parse opportunities from file
# ============================================================

def parse_opportunities_file(
    path: str,
) -> list[dict[str, Any]]:
    """
    Read an opportunity text file and parse its contents.
    """

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        text = file.read()

    return parse_opportunities(text)