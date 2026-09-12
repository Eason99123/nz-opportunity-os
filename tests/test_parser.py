from src.parser import parse_opportunities


def test_parse_opportunities_extracts_fields() -> None:
    text = """
Title: Big Tech: Too Big To Fail?
Type: Talk/Discussion
Where: Sir Owen G Glenn Building, Auckland
Date/Deadline: Wednesday, April 15, 5:15 PM
Why fit: Useful industry context for a first-year CS student.
Next step: Check the event page and register.
Source link: https://example.com/big-tech
Relevance: 4/5
Beginner Fit: 4/5
Career Value: 3/5
Practicality: 5/5
University Fit: 5/5
Total Score: 21/25
"""

    results = parse_opportunities(text)

    assert len(results) == 1

    item = results[0]
    assert item["title"] == "Big Tech: Too Big To Fail?"
    assert item["type"] == "Talk/Discussion"
    assert item["where"] == "Sir Owen G Glenn Building, Auckland"
    assert item["relevance"] == 4
    assert item["beginner_fit"] == 4
    assert item["total_score"] == 21