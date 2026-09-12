from src.ranking import (
    deduplicate_opportunities,
    get_best_opportunity,
    sort_opportunities,
)


def test_deduplicate_opportunities_keeps_higher_score() -> None:
    opportunities = [
        {
            "title": "Big Tech: Too Big To Fail?",
            "total_score": 16,
            "source_link": "https://example.com/low",
        },
        {
            "title": "Big Tech: Too Big To Fail?",
            "total_score": 21,
            "source_link": "https://example.com/high",
        },
        {
            "title": "Peak Performance & AI - May Meetup",
            "total_score": 23,
            "source_link": "https://example.com/peak",
        },
    ]

    deduplicated = deduplicate_opportunities(opportunities)

    assert len(deduplicated) == 2

    kept_big_tech = next(item for item in deduplicated if item["title"] == "Big Tech: Too Big To Fail?")
    assert kept_big_tech["total_score"] == 21
    assert kept_big_tech["source_link"] == "https://example.com/high"


def test_sort_opportunities_orders_by_total_score_desc() -> None:
    opportunities = [
        {"title": "A", "total_score": 10},
        {"title": "B", "total_score": 25},
        {"title": "C", "total_score": 18},
    ]

    ranked = sort_opportunities(opportunities)

    assert ranked[0]["title"] == "B"
    assert ranked[1]["title"] == "C"
    assert ranked[2]["title"] == "A"


def test_get_best_opportunity_returns_first_ranked_item() -> None:
    opportunities = [
        {"title": "Peak Performance & AI - May Meetup", "total_score": 23},
        {"title": "Big Tech: Too Big To Fail?", "total_score": 21},
    ]

    best = get_best_opportunity(opportunities)

    assert best is not None
    assert best["title"] == "Peak Performance & AI - May Meetup"
    assert best["total_score"] == 23