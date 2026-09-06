"""Persistence for postings.json: the tracker's memory.

The one rule everything else depends on: `first_seen_at` is stamped by our
own clock the first time a (company, ats, source_id) key is observed, and
is never rewritten afterwards. ATS-provided timestamps are not trustworthy
for this (Workday gives relative strings, employers re-publish listings),
so "new" means "new to us," full stop.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

Posting = dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _key(posting: Posting) -> tuple[str, str, str]:
    return (posting["company"], posting["ats"], posting["source_id"])


def load_postings(path: Path) -> list[Posting]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_postings(path: Path, postings: list[Posting]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(postings, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def merge_postings(existing: list[Posting], observed: list[Posting]) -> tuple[list[Posting], int]:
    """Merge freshly-observed postings into the existing store.

    Returns (merged_list, count_of_new_postings). Existing entries are
    never dropped just because this poll didn't see them again — a
    transient per-company failure shouldn't erase history.
    """
    by_key: dict[tuple[str, str, str], Posting] = {_key(p): dict(p) for p in existing}
    new_count = 0
    stamp = now_iso()

    for posting in observed:
        key = _key(posting)
        if key in by_key:
            entry = by_key[key]
            entry["last_seen_at"] = stamp
            entry["title"] = posting["title"]
            entry["location"] = posting["location"]
            entry["url"] = posting["url"]
        else:
            entry = dict(posting)
            entry["first_seen_at"] = stamp
            entry["last_seen_at"] = stamp
            by_key[key] = entry
            new_count += 1

    return list(by_key.values()), new_count
