import json
from pathlib import Path

from radar.ats_clients import parse_ashby, parse_greenhouse, parse_teamtailor

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    with (FIXTURES / name).open() as f:
        return json.load(f)


def test_parse_greenhouse_normalizes_shape():
    data = _load("greenhouse_sample.json")
    postings = parse_greenhouse("Acme", data)
    assert len(postings) == 5
    first = postings[0]
    assert first["source_id"] == "1001"
    assert first["company"] == "Acme"
    assert first["ats"] == "greenhouse"
    assert first["title"] == "Product Manager Intern, Summer 2027"
    assert first["location"] == "San Francisco, CA"
    assert first["department"] == "Product"


def test_parse_ashby_normalizes_shape():
    data = _load("ashby_sample.json")
    postings = parse_ashby("Beta", data)
    assert len(postings) == 3
    first = postings[0]
    assert first["source_id"] == "ab-2001"
    assert first["ats"] == "ashby"
    assert first["title"].startswith("Technical Product Manager")


def test_parse_teamtailor_normalizes_shape():
    data = _load("teamtailor_sample.json")
    postings = parse_teamtailor("Acme", data)
    assert len(postings) == 2
    first = postings[0]
    assert first["source_id"] == "3001"
    assert first["company"] == "Acme"
    assert first["ats"] == "teamtailor"
    assert first["title"] == "Software Engineering Intern, Summer 2027"
    assert first["url"] == "https://careers.acme.example/jobs/3001-software-engineering-intern"
    assert first["posted_at"] == "2026-09-01T10:00:00+01:00"


def test_parse_teamtailor_expands_gb_country_code():
    # classify.is_uk_location doesn't recognize bare ISO codes, only names/cities,
    # so the raw "GB" from Teamtailor's structured address must be expanded here.
    data = _load("teamtailor_sample.json")
    postings = parse_teamtailor("Acme", data)
    assert postings[0]["location"] == "London, United Kingdom"
    assert postings[1]["location"] == "Barcelona, ES"
