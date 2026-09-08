"""Regex-based classifier: is this posting a Summer 2027 internship or
placement?

Sibling to `radar/classify.py` (the PM/UX tracker's classifier) — reuses its
year-cycle and UK-location logic, which aren't role-specific. Unlike the PM
tracker, this one doesn't filter by role/title keyword at all: the company
registry (`data/companies_engineering.yaml`) is itself scoped to a curated
list of UK engineering employers, so every Summer 2027 internship/placement
any of them posts is in scope — mechanical, electrical, software, commercial
analyst, whatever the discipline.
"""
from __future__ import annotations

import re

from radar.classify import is_uk_location, looks_like_2027_cycle  # noqa: F401 — re-exported

PLACEMENT_PATTERN = re.compile(
    r"\b(intern(?:ship)?s?|placements?|industrial\s*placements?|year\s*in\s*industry|"
    r"vacation\s*(?:program(?:me)?|scheme)|summer\s*(?:program(?:me)?|scheme|work\s*experience))\b",
    re.IGNORECASE,
)

EXCLUDE_PATTERN = re.compile(r"\b(manager\s+of\s+interns?|internship\s+coordinator)\b", re.IGNORECASE)


def is_internship(title: str) -> bool:
    """True for any internship/placement-shaped title — no role filtering,
    since the company list itself is what scopes this tracker to engineering
    employers.
    """
    if EXCLUDE_PATTERN.search(title):
        return False
    return bool(PLACEMENT_PATTERN.search(title))


def is_relevant(title: str) -> bool:
    return is_internship(title) and looks_like_2027_cycle(title)


def is_relevant_uk(title: str, location: str | None) -> bool:
    return is_relevant(title) and is_uk_location(location)
