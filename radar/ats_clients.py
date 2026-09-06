"""Thin clients for the public, unauthenticated job-board APIs behind most
company careers pages. Every function returns a list of postings normalized
to the same shape:

    {"source_id": str, "company": str, "ats": str, "title": str,
     "location": str, "url": str, "posted_at": str | None,
     "department": str | None}

A `requests.exceptions.RequestException` propagates to the caller (poll.py)
so one bad company never silently produces fake "empty" results.
"""
from __future__ import annotations

import time
from typing import Any

import requests

USER_AGENT = "pm-internship-radar/1.0 (+https://github.com/; contact via repo issues)"
TIMEOUT = (5, 15)  # (connect, read) — bounds hangs even when DNS/connect stalls past the read timeout
_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


class TokenError(Exception):
    """Raised when a company's ATS token/tenant/site looks wrong (404/invalid)."""


def _get(url: str, **kwargs) -> requests.Response:
    resp = _session.get(url, timeout=TIMEOUT, **kwargs)
    if resp.status_code == 429:
        time.sleep(2)
        resp = _session.get(url, timeout=TIMEOUT, **kwargs)
    return resp


def _post(url: str, **kwargs) -> requests.Response:
    resp = _session.post(url, timeout=TIMEOUT, **kwargs)
    if resp.status_code == 429:
        time.sleep(2)
        resp = _session.post(url, timeout=TIMEOUT, **kwargs)
    return resp


def parse_greenhouse(company: str, data: dict) -> list[dict[str, Any]]:
    postings = []
    for job in data.get("jobs", []):
        departments = job.get("departments") or []
        dept = departments[0]["name"] if departments else None
        location = (job.get("location") or {}).get("name", "")
        postings.append({
            "source_id": str(job["id"]),
            "company": company,
            "ats": "greenhouse",
            "title": job.get("title", ""),
            "location": location,
            "url": job.get("absolute_url", ""),
            "posted_at": job.get("first_published") or job.get("updated_at"),
            "department": dept,
        })
    return postings


def fetch_greenhouse(company: str, token: str) -> list[dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    resp = _get(url)
    if resp.status_code == 404:
        raise TokenError(f"greenhouse: no board for token {token!r}")
    resp.raise_for_status()
    return parse_greenhouse(company, resp.json())


def parse_ashby(company: str, data: dict) -> list[dict[str, Any]]:
    postings = []
    for job in data.get("jobs", []):
        location = job.get("location", "")
        postings.append({
            "source_id": str(job["id"]),
            "company": company,
            "ats": "ashby",
            "title": job.get("title", ""),
            "location": location,
            "url": job.get("jobUrl") or job.get("applyUrl", ""),
            "posted_at": job.get("publishedAt"),
            "department": job.get("department"),
        })
    return postings


def fetch_ashby(company: str, token: str) -> list[dict[str, Any]]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    resp = _get(url)
    if resp.status_code == 404:
        raise TokenError(f"ashby: no board for token {token!r}")
    resp.raise_for_status()
    return parse_ashby(company, resp.json())


def parse_lever(company: str, data: list) -> list[dict[str, Any]]:
    postings = []
    for job in data:
        categories = job.get("categories") or {}
        postings.append({
            "source_id": str(job["id"]),
            "company": company,
            "ats": "lever",
            "title": job.get("text", ""),
            "location": categories.get("location", ""),
            "url": job.get("hostedUrl", ""),
            "posted_at": job.get("createdAt"),
            "department": categories.get("team"),
        })
    return postings


def fetch_lever(company: str, token: str) -> list[dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    resp = _get(url)
    if resp.status_code == 404:
        raise TokenError(f"lever: wrong token {token!r} (404)")
    resp.raise_for_status()
    return parse_lever(company, resp.json())


def fetch_workday(company: str, tenant: str, dc: str, site: str) -> list[dict[str, Any]]:
    url = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    all_postings: list[dict[str, Any]] = []
    offset = 0
    limit = 20
    while True:
        body = {"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}
        resp = _post(url, json=body)
        if resp.status_code in (404, 400):
            raise TokenError(f"workday: bad tenant/dc/site {tenant}/{dc}/{site}")
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("jobPostings", [])
        for job in jobs:
            external_path = job.get("externalPath", "")
            all_postings.append({
                "source_id": external_path or job.get("title", ""),
                "company": company,
                "ats": "workday",
                "title": job.get("title", ""),
                "location": job.get("locationsText", ""),
                "url": f"https://{tenant}.{dc}.myworkdayjobs.com/{site}{external_path}",
                "posted_at": None,  # relative string only ("Posted 3 Days Ago"); unusable for dedup
                "department": None,
            })
        total = data.get("total", len(jobs))
        offset += limit
        if offset >= total or not jobs:
            break
        time.sleep(0.3)
    return all_postings


def parse_smartrecruiters(company: str, data: dict) -> list[dict[str, Any]]:
    postings = []
    for job in data.get("content", []):
        loc = job.get("location") or {}
        location = ", ".join(p for p in [loc.get("city"), loc.get("region"), loc.get("country")] if p)
        postings.append({
            "source_id": str(job["id"]),
            "company": company,
            "ats": "smartrecruiters",
            "title": job.get("name", ""),
            "location": location,
            "url": job.get("ref", ""),
            "posted_at": job.get("releasedDate"),
            "department": None,
        })
    return postings


def fetch_smartrecruiters(company: str, token: str) -> list[dict[str, Any]]:
    url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100"
    resp = _get(url)
    if resp.status_code == 404:
        raise TokenError(f"smartrecruiters: no company for token {token!r}")
    resp.raise_for_status()
    return parse_smartrecruiters(company, resp.json())


def fetch_for_company(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Dispatch to the right client based on an entry from companies.yaml."""
    ats = entry["ats"]
    name = entry["name"]
    if ats == "greenhouse":
        return fetch_greenhouse(name, entry["token"])
    if ats == "ashby":
        return fetch_ashby(name, entry["token"])
    if ats == "lever":
        return fetch_lever(name, entry["token"])
    if ats == "workday":
        return fetch_workday(name, entry["tenant"], entry["dc"], entry["site"])
    if ats == "smartrecruiters":
        return fetch_smartrecruiters(name, entry["token"])
    raise ValueError(f"unknown ats {ats!r} for company {name!r}")
