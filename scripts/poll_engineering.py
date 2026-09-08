"""Poll every company in data/companies_engineering.yaml, classify postings
as Summer 2027 internships/placements, and merge results into
data/postings_engineering.json.

Sibling to scripts/poll.py (the PM/UX tracker's poller) — identical shape,
different data files and classifier. One company's failure never aborts the
run — each call is wrapped in its own try/except so a single flaky ATS
doesn't take down the whole tracker.
"""
from __future__ import annotations

import functools
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

import yaml

print = functools.partial(print, flush=True)  # noqa: A001 — always flush so CI/background logs show progress

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar.ats_clients import fetch_for_company  # noqa: E402
from radar.classify_engineering import is_relevant_uk  # noqa: E402
from radar.storage import load_postings, merge_postings, save_postings  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
COMPANIES_PATH = ROOT / "data" / "companies_engineering.yaml"
POSTINGS_PATH = ROOT / "data" / "postings_engineering.json"
PER_COMPANY_TIMEOUT = 60.0  # generous — Workday pagination for a big employer can take a while


def fetch_with_timeout(entry: dict, timeout: float = PER_COMPANY_TIMEOUT):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fetch_for_company, entry)
    return future.result(timeout=timeout)


def main() -> None:
    if not COMPANIES_PATH.exists():
        print(f"No {COMPANIES_PATH} yet — run scripts/discover_companies_engineering.py first.")
        return

    with COMPANIES_PATH.open(encoding="utf-8") as f:
        companies = yaml.safe_load(f) or []

    existing = load_postings(POSTINGS_PATH)

    all_relevant = []
    checked = 0
    failed = 0

    for entry in companies:
        name = entry["name"]
        try:
            postings = fetch_with_timeout(entry)
            checked += 1
        except FutureTimeoutError:
            failed += 1
            print(f"  FAILED  {name}: timed out after {PER_COMPANY_TIMEOUT:.0f}s")
            time.sleep(0.5)
            continue
        except Exception as exc:  # noqa: BLE001 — one bad company must not abort the run
            failed += 1
            print(f"  FAILED  {name}: {exc}")
            time.sleep(0.5)
            continue

        relevant = [p for p in postings if is_relevant_uk(p["title"], p["location"])]
        all_relevant.extend(relevant)
        if relevant:
            print(f"  {name}: {len(relevant)} relevant posting(s) of {len(postings)} total")
        time.sleep(0.5)

    merged, new_count = merge_postings(existing, all_relevant)
    save_postings(POSTINGS_PATH, merged)

    print(
        f"\n{new_count} new postings across {checked} companies checked, "
        f"{failed} companies failed. {len(merged)} total tracked postings."
    )


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    sys.stderr.flush()
    import os
    os._exit(0)
