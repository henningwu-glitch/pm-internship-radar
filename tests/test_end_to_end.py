import json
from pathlib import Path

from radar.ats_clients import parse_ashby, parse_greenhouse
from radar.classify import is_relevant, is_relevant_uk
from radar.storage import merge_postings

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    with (FIXTURES / name).open() as f:
        return json.load(f)


def test_pipeline_keeps_only_pm_relevant_postings():
    gh_postings = parse_greenhouse("Acme", _load("greenhouse_sample.json"))
    ab_postings = parse_ashby("Beta", _load("ashby_sample.json"))
    all_postings = gh_postings + ab_postings

    relevant = [p for p in all_postings if is_relevant(p["title"])]
    titles = sorted(p["title"] for p in relevant)

    # Scope now covers PM, Product Owner, and UX/product-design internships.
    assert titles == [
        "APM Intern",
        "Product Design Intern",
        "Product Manager Intern, Summer 2027",
        "Product Manager Intern, Summer 2027",
        "Technical Product Manager Internship - Summer 2027",
    ]

    merged, new_count = merge_postings([], relevant)
    assert new_count == 5
    assert all("first_seen_at" in p for p in merged)


def test_pipeline_keeps_only_uk_pm_postings():
    """This mirrors what scripts/poll.py actually runs in production: PM
    relevance AND a UK location, since the tracker is scoped to UK Summer
    2027 PM internships specifically.
    """
    gh_postings = parse_greenhouse("Acme", _load("greenhouse_sample.json"))
    ab_postings = parse_ashby("Beta", _load("ashby_sample.json"))
    all_postings = gh_postings + ab_postings

    uk_relevant = [p for p in all_postings if is_relevant_uk(p["title"], p["location"])]

    assert len(uk_relevant) == 1
    assert uk_relevant[0]["location"] == "London, United Kingdom"
    assert uk_relevant[0]["title"] == "Product Manager Intern, Summer 2027"
