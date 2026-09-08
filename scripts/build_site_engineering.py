"""Render data/postings_engineering.json into site/engineering.html using
site/template_engineering.html.

Sibling to scripts/build_site.py (the PM/UX tracker's site builder) —
identical shape, different data/template files.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from radar.storage import load_postings  # noqa: E402

TEMPLATE_PATH = ROOT / "site" / "template_engineering.html"
OUTPUT_PATH = ROOT / "site" / "engineering.html"
POSTINGS_PATH = ROOT / "data" / "postings_engineering.json"
COMPANIES_PATH = ROOT / "data" / "companies_engineering.yaml"


def main() -> None:
    postings = load_postings(POSTINGS_PATH)

    if COMPANIES_PATH.exists():
        with COMPANIES_PATH.open(encoding="utf-8") as f:
            companies = yaml.safe_load(f) or []
    else:
        companies = []

    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "companies_watched": len(companies),
    }

    def to_embeddable_json(obj) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace(
        "__POSTINGS_JSON__", to_embeddable_json(postings)
    ).replace(
        "__META_JSON__", to_embeddable_json(meta)
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(postings)} postings, {len(companies)} companies watched)")


if __name__ == "__main__":
    main()
