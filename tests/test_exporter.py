from pathlib import Path

from src.exporter import save_markdown_summary, save_to_csv, save_to_json


def test_save_to_json_creates_file_and_writes_content(tmp_path: Path) -> None:
    output_file = tmp_path / "output.json"
    data = {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "count": 1,
        "best_opportunity": {"title": "Peak Performance & AI - May Meetup"},
        "next_actions": ["Register on Eventbrite."],
        "opportunities": [
            {"title": "Peak Performance & AI - May Meetup", "total_score": 23}
        ],
    }

    save_to_json(data, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "Peak Performance & AI - May Meetup" in content
    assert '"count": 1' in content


def test_save_to_csv_creates_file_and_writes_rows(tmp_path: Path) -> None:
    output_file = tmp_path / "output.csv"
    opportunities = [
        {
            "title": "Peak Performance & AI - May Meetup",
            "type": "Tech Meetup",
            "where": "Microsoft, Auckland",
            "date_deadline": "Monday, May 4, 5:30 PM",
            "why_fit": "Good networking opportunity and AI-related learning.",
            "next_step": "Register on Eventbrite.",
            "source_link": "https://example.com/peak",
            "relevance": 5,
            "beginner_fit": 4,
            "career_value": 4,
            "practicality": 5,
            "university_fit": 5,
            "total_score": 23,
        }
    ]

    save_to_csv(opportunities, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "title,type,where" in content
    assert "Peak Performance & AI - May Meetup" in content
    assert "Microsoft, Auckland" in content


def test_save_markdown_summary_creates_readable_summary(tmp_path: Path) -> None:
    output_file = tmp_path / "summary.md"
    opportunities = [
        {
            "title": "Peak Performance & AI - May Meetup",
            "type": "Tech Meetup",
            "where": "Microsoft, Auckland",
            "date_deadline": "Monday, May 4, 5:30 PM",
            "why_fit": "Good networking opportunity and AI-related learning.",
            "next_step": "Register on Eventbrite.",
            "source_link": "https://example.com/peak",
            "relevance": 5,
            "beginner_fit": 4,
            "career_value": 4,
            "practicality": 5,
            "university_fit": 5,
            "total_score": 23,
        }
    ]
    actions = [
        "Open the source link.",
        "Add the event to your calendar.",
        "Register on Eventbrite.",
    ]

    save_markdown_summary(opportunities, actions, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "# Weekly Opportunity Summary" in content
    assert "## Best Opportunity" in content
    assert "Peak Performance & AI - May Meetup" in content
    assert "## Next 3 Actions" in content
    assert "Register on Eventbrite." in content