import json

from radar.storage import load_postings, merge_postings, save_postings

SAMPLE_POSTING = {
    "source_id": "42",
    "company": "Acme",
    "ats": "greenhouse",
    "title": "Product Manager Intern, Summer 2027",
    "location": "Remote",
    "url": "https://job-boards.greenhouse.io/acme/jobs/42",
    "posted_at": "2026-09-01T00:00:00Z",
    "department": "Product",
}


def test_first_poll_creates_first_seen_at():
    merged, new_count = merge_postings([], [SAMPLE_POSTING])
    assert new_count == 1
    assert len(merged) == 1
    assert merged[0]["first_seen_at"] == merged[0]["last_seen_at"]


def test_second_poll_does_not_reset_first_seen_at_or_duplicate():
    merged_once, _ = merge_postings([], [SAMPLE_POSTING])
    original_first_seen = merged_once[0]["first_seen_at"]

    merged_twice, new_count = merge_postings(merged_once, [SAMPLE_POSTING])

    assert new_count == 0
    assert len(merged_twice) == 1
    assert merged_twice[0]["first_seen_at"] == original_first_seen


def test_missing_posting_is_not_dropped():
    merged_once, _ = merge_postings([], [SAMPLE_POSTING])
    merged_twice, new_count = merge_postings(merged_once, [])  # this poll saw nothing
    assert new_count == 0
    assert len(merged_twice) == 1  # old entry survives


def test_genuinely_new_posting_gets_appended():
    other = dict(SAMPLE_POSTING, source_id="99", title="APM Intern")
    merged_once, _ = merge_postings([], [SAMPLE_POSTING])
    merged_twice, new_count = merge_postings(merged_once, [SAMPLE_POSTING, other])
    assert new_count == 1
    assert len(merged_twice) == 2


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "postings.json"
    merged, _ = merge_postings([], [SAMPLE_POSTING])
    save_postings(path, merged)

    loaded = load_postings(path)
    assert loaded == merged

    with path.open() as f:
        raw = json.load(f)
    assert raw[0]["source_id"] == "42"


def test_load_missing_file_returns_empty_list(tmp_path):
    assert load_postings(tmp_path / "does_not_exist.json") == []
