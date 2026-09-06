"""Poll every company in data/companies.yaml, classify postings for PM
relevance, and merge results into data/postings.json.

One company's failure never aborts the run — each call is wrapped in its
own try/except so a single flaky ATS doesn't take down the whole tracker.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar.ats_clients import fetch_for_company  # noqa: E402
from radar.classify import is_relevant  # noqa: E402
from radar.storage import load_postings, merge_postings, save_postings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
COMPANIES_PATH = ROOT / "data" / "companies.yaml"
POSTINGS_PATH = ROOT / "data" / "postings.json"


def main() -> None:
    with COMPANIES_PATH.open(encoding="utf-8") as f:
        companies = yaml.safe_load(f) or []

    existing = load_postings(POSTINGS_PATH)

    all_relevant = []
    checked = 0
    failed = 0

    for entry in companies:
        name = entry["name"]
        try:
            postings = fetch_for_company(entry)
            checked += 1
        except Exception as exc:  # noqa: BLE001 — one bad company must not abort the run
            failed += 1
            print(f"  FAILED  {name}: {exc}")
            time.sleep(0.5)
            continue

        relevant = [p for p in postings if is_relevant(p["title"])]
        all_relevant.extend(relevant)
        if relevant:
            print(f"  {name}: {len(relevant)} PM-relevant posting(s) of {len(postings)} total")
        time.sleep(0.5)

    merged, new_count = merge_postings(existing, all_relevant)
    save_postings(POSTINGS_PATH, merged)

    print(
        f"\n{new_count} new postings across {checked} companies checked, "
        f"{failed} companies failed. {len(merged)} total tracked postings."
    )


if __name__ == "__main__":
    main()
