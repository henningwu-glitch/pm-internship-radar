"""Regex-based classifier: is this posting a Product Manager internship
relevant to the Summer 2027 cycle? Titles are formulaic enough that a
curated regex set beats a trained model here, and it's fully inspectable.
"""
from __future__ import annotations

import re

INTERN_PATTERN = re.compile(r"\bintern(?:ship)?s?\b", re.IGNORECASE)

PM_PATTERNS = [
    re.compile(r"\bproduct\s*manager\b", re.IGNORECASE),
    re.compile(r"\bproduct\s*management\b", re.IGNORECASE),
    re.compile(r"\bAPM\b"),  # Associate Product Manager — case-sensitive, avoids "apm" false positives
    re.compile(r"\bassociate\s*product\s*manager\b", re.IGNORECASE),
    re.compile(r"\btechnical\s*product\s*manager\b", re.IGNORECASE),
]

EXCLUDE_PATTERN = re.compile(r"\b(manager\s+of\s+interns?|internship\s+coordinator)\b", re.IGNORECASE)

YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


def is_pm_internship(title: str) -> bool:
    if EXCLUDE_PATTERN.search(title):
        return False
    if not INTERN_PATTERN.search(title):
        return False
    return any(p.search(title) for p in PM_PATTERNS)


def looks_like_2027_cycle(title: str) -> bool:
    """True unless the title explicitly names 2026 or an earlier year.

    Many companies don't add a year to the title until applications
    actually open, so "no year mentioned" is treated as included rather
    than excluded — otherwise real early postings would be silently hidden.
    """
    match = YEAR_PATTERN.search(title)
    if not match:
        return True
    return int(match.group(1)) >= 2027


def is_relevant(title: str) -> bool:
    return is_pm_internship(title) and looks_like_2027_cycle(title)
