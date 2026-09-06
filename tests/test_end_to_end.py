import json
from pathlib import Path

from radar.ats_clients import parse_ashby, parse_greenhouse
from radar.classify import is_relevant
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

    assert titles == [
        "APM Intern",
        "Product Manager Intern, Summer 2027",
        "Technical Product Manager Internship - Summer 2027",
    ]

    merged, new_count = merge_postings([], relevant)
    assert new_count == 3
    assert all("first_seen_at" in p for p in merged)
