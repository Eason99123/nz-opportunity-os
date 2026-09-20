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

def test_parser_supports_company_field():
    text = """
Title: Engineering Summer Intern
Company: Microchip Technology
Type: Internship
Where: Auckland, New Zealand
Source Link: https://example.com/job
"""

    result = parse_opportunities(text)

    assert len(result) == 1
    assert result[0]["company"] == "Microchip Technology"


def test_parser_supports_source_type_field():
    text = """
Title: Software Engineering Intern
Company: Example Company
Type: Internship
Source Link: https://www.linkedin.com/jobs/view/123
Source Type: THIRD_PARTY
"""

    result = parse_opportunities(text)

    assert len(result) == 1
    assert result[0]["source_type"] == "THIRD_PARTY"


def test_parser_supports_company_and_source_type_together():
    text = """
Title: Test Automation Framework Development
Company: Microchip Technology
Type: Internship
Where: Auckland, New Zealand
Date Deadline: 30 September 2026
Why Fit: Python automation and testing experience.
Next Step: Apply through the employer application page.
Source Link: https://www.linkedin.com/jobs/view/123
Source Type: THIRD_PARTY
Relevance: 5
Beginner Fit: 5
Career Value: 5
Practicality: 5
University Fit: 5
Total Score: 25
"""

    result = parse_opportunities(text)

    assert len(result) == 1

    opportunity = result[0]

    assert opportunity["title"] == (
        "Test Automation Framework Development"
    )
    assert opportunity["company"] == "Microchip Technology"
    assert opportunity["source_type"] == "THIRD_PARTY"
    assert opportunity["where"] == "Auckland, New Zealand"
    assert opportunity["total_score"] == 25


def test_old_schema_still_works_without_company():
    text = """
Title: AWS Cloud and AI Day Auckland
Type: Free cloud, AI, developer and networking event
Where: Auckland
Date Deadline: 22 September 2026
Source Link: https://aws.amazon.com/events/example
Relevance: 5
Total Score: 24
"""

    result = parse_opportunities(text)

    assert len(result) == 1

    opportunity = result[0]

    assert opportunity["title"] == "AWS Cloud and AI Day Auckland"
    assert "company" not in opportunity
    assert "source_type" not in opportunity
    assert opportunity["total_score"] == 24


def test_unknown_fields_are_ignored():
    text = """
Title: Software Internship
Company: Example Company
Random Field: This should not be stored
Another Unknown Field: Ignore this too
Source Link: https://example.com/job
"""

    result = parse_opportunities(text)

    opportunity = result[0]

    assert "random_field" not in opportunity
    assert "another_unknown_field" not in opportunity
    assert opportunity["company"] == "Example Company"