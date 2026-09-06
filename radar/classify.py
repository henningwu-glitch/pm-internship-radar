"""Regex-based classifier: is this posting a Product Manager / Product Owner
/ UX internship relevant to the Summer 2027 cycle? Titles are formulaic
enough that a curated regex set beats a trained model here, and it's fully
inspectable.
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

PO_PATTERNS = [
    re.compile(r"\bproduct\s*owner\b", re.IGNORECASE),
]

UX_PATTERNS = [
    re.compile(r"\bUX\b"),  # case-sensitive like APM — avoids stray lowercase "ux" substrings
    re.compile(r"\bUX\s*design(?:er)?\b", re.IGNORECASE),
    re.compile(r"\buser\s*experience\b", re.IGNORECASE),
    re.compile(r"\bproduct\s*design(?:er)?\b", re.IGNORECASE),
    re.compile(r"\buser\s*research(?:er)?\b", re.IGNORECASE),
]

ROLE_PATTERNS = PM_PATTERNS + PO_PATTERNS + UX_PATTERNS

EXCLUDE_PATTERN = re.compile(r"\b(manager\s+of\s+interns?|internship\s+coordinator)\b", re.IGNORECASE)

YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


def is_pm_internship(title: str) -> bool:
    """Despite the name (kept for compatibility with existing call sites),
    this matches Product Manager, Product Owner, and UX/product-design
    internships alike — the tracker's scope was broadened to all three.
    """
    if EXCLUDE_PATTERN.search(title):
        return False
    if not INTERN_PATTERN.search(title):
        return False
    return any(p.search(title) for p in ROLE_PATTERNS)


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


UK_COUNTRY_PATTERN = re.compile(r"\b(united kingdom|u\.k\.|uk)\b", re.IGNORECASE)
UK_NATION_PATTERN = re.compile(r"\b(england|scotland|wales|northern ireland)\b", re.IGNORECASE)
NOT_UK_PATTERN = re.compile(r"\b(ontario|canada)\b", re.IGNORECASE)  # guards "London, Ontario"
UK_CITIES = {
    # Deliberately excludes ambiguous names with a well-known US namesake
    # that would false-positive on substring matching — York (New York),
    # Cambridge (Cambridge, MA), Birmingham (Birmingham, AL), Bristol
    # (Bristol, CT/RI/VA), Reading (Reading, PA), Aberdeen (Aberdeen, MD/WA).
    "london", "manchester", "edinburgh", "glasgow", "leeds", "belfast",
    "cardiff", "liverpool", "sheffield", "nottingham", "leicester",
    "milton keynes", "cheltenham",
}


def is_uk_location(location: str | None) -> bool:
    """True if a posting's location string points to the UK.

    Country/nation names are checked first since they're unambiguous. City
    names are checked second but only after ruling out "Ontario"/"Canada"
    in the same string, since "London" alone is also a real Canadian city.
    """
    if not location:
        return False
    if NOT_UK_PATTERN.search(location):
        return False
    if UK_COUNTRY_PATTERN.search(location) or UK_NATION_PATTERN.search(location):
        return True
    loc_lower = location.lower()
    return any(city in loc_lower for city in UK_CITIES)


def is_relevant(title: str) -> bool:
    return is_pm_internship(title) and looks_like_2027_cycle(title)


def is_relevant_uk(title: str, location: str | None) -> bool:
    return is_relevant(title) and is_uk_location(location)
