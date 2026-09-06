import json
from pathlib import Path

from radar.ats_clients import parse_ashby, parse_greenhouse

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
