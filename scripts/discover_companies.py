"""Build data/companies.yaml: a wide, VERIFIED registry of companies whose
public ATS job-board API we can poll directly.

Three passes, per the build brief:
  1. Mine the open-source internship trackers (SimplifyJobs, vanshb03,
     zshah101) for ATS URLs already embedded in their README tables.
  2. Add a curated list of known PM-heavy employers (consumer product,
     fintech, design-forward) and resolve their ATS token by probing
     common guesses.
  3. Verify every single candidate with a live call to its endpoint.
     Anything that 404s / errors is dropped rather than guessed at —
     an unverified entry fails silently forever, which is worse than
     not tracking the company at all.

Usage: python scripts/discover_companies.py
"""
from __future__ import annotations

import functools
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

import requests
import yaml

socket.setdefaulttimeout(20)  # belt-and-suspenders: guards against DNS/connect hangs on Windows
print = functools.partial(print, flush=True)  # noqa: A001 — always flush so background logs show progress

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar.ats_clients import USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "companies.yaml"

README_SOURCES = [
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/README.md",
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/main/README.md",
    "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/main/README.md",
    "https://raw.githubusercontent.com/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/main/README.md",
]

HEADERS = {"User-Agent": "pm-internship-radar/1.0 (company discovery)"}

TR_RE = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
COMPANY_NAME_RE = re.compile(r'<strong>\s*<a[^>]*>([^<]+)</a>\s*</strong>')
GREENHOUSE_URL_RE = re.compile(r"(?:job-boards|boards)\.greenhouse\.io/([a-zA-Z0-9_-]+)")
LEVER_URL_RE = re.compile(r"jobs\.lever\.co/([a-zA-Z0-9_.-]+)")
ASHBY_URL_RE = re.compile(r"jobs\.ashbyhq\.com/([a-zA-Z0-9_.-]+)")
WORKDAY_URL_RE = re.compile(
    r"https://([a-zA-Z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-zA-Z-]{2,5}/)?([a-zA-Z0-9_-]+)/job/"
)
SMARTRECRUITERS_URL_RE = re.compile(r"smartrecruiters\.com/([a-zA-Z0-9_-]+)/")


def fetch_text(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=(5, 20))
        if resp.status_code == 200 and len(resp.text) > 500:
            return resp.text
    except requests.exceptions.RequestException:
        pass
    return None


def parse_readme(text: str) -> dict[tuple[str, str], dict]:
    """Extract {(ats, token_key): candidate} from one README's HTML tables."""
    candidates: dict[tuple[str, str], dict] = {}
    current_company = None
    for row in TR_RE.findall(text):
        name_match = COMPANY_NAME_RE.search(row)
        if name_match:
            current_company = name_match.group(1).strip()
        if not current_company:
            continue

        gh = GREENHOUSE_URL_RE.search(row)
        if gh:
            token = gh.group(1)
            candidates[("greenhouse", token)] = {
                "name": current_company, "ats": "greenhouse", "token": token,
            }
        lv = LEVER_URL_RE.search(row)
        if lv:
            token = lv.group(1)
            candidates[("lever", token)] = {
                "name": current_company, "ats": "lever", "token": token,
            }
        ab = ASHBY_URL_RE.search(row)
        if ab:
            token = ab.group(1)
            candidates[("ashby", token)] = {
                "name": current_company, "ats": "ashby", "token": token,
            }
        sr = SMARTRECRUITERS_URL_RE.search(row)
        if sr:
            token = sr.group(1)
            candidates[("smartrecruiters", token)] = {
                "name": current_company, "ats": "smartrecruiters", "token": token,
            }
        wd = WORKDAY_URL_RE.search(row)
        if wd:
            tenant, dc, site = wd.group(1), wd.group(2), wd.group(3)
            candidates[("workday", f"{tenant}/{dc}/{site}")] = {
                "name": current_company, "ats": "workday",
                "tenant": tenant, "dc": dc, "site": site,
            }
    return candidates


# --- Pass 2: known PM-heavy employers not reliably covered by pass 1 ---
# {display name: [(ats, token_or_tuple), ...]} — a company may list a couple
# of guesses; only the ones that verify in pass 3 survive.
KNOWN_PM_EMPLOYERS: dict[str, list[tuple]] = {
    "Airbnb": [("greenhouse", "airbnb")],
    "Stripe": [("greenhouse", "stripe")],
    "Notion": [("greenhouse", "notion")],
    "Figma": [("greenhouse", "figma")],
    "Duolingo": [("greenhouse", "duolingo")],
    "Instacart": [("greenhouse", "instacart")],
    "Robinhood": [("greenhouse", "robinhood")],
    "Coinbase": [("greenhouse", "coinbase")],
    "Asana": [("greenhouse", "asana")],
    "Linear": [("ashby", "linear")],
    "Ramp": [("ashby", "ramp")],
    "Pinterest": [("greenhouse", "pinterest")],
    "Affirm": [("greenhouse", "affirm")],
    "Discord": [("greenhouse", "discord")],
    "Reddit": [("greenhouse", "reddit")],
    "Squarespace": [("greenhouse", "squarespace")],
    "Dropbox": [("greenhouse", "dropbox")],
    "Vercel": [("greenhouse", "vercel")],
    "Retool": [("greenhouse", "retool")],
    "Plaid": [("greenhouse", "plaid")],
    "Palantir Technologies": [("lever", "palantir")],
    "DoorDash": [("greenhouse", "doordash")],
    "Lyft": [("greenhouse", "lyft")],
    "Etsy": [("greenhouse", "etsy")],
    "Yelp": [("greenhouse", "yelp")],
    "Grammarly": [("greenhouse", "grammarly")],
    "Canva": [("greenhouse", "canva")],
    "Miro": [("greenhouse", "miro")],
    "Webflow": [("greenhouse", "webflow")],
    "Brex": [("greenhouse", "brex")],
    "Rippling": [("greenhouse", "rippling")],
    "Gusto": [("greenhouse", "gusto")],
    "Snap Inc": [("greenhouse", "snapchat")],
    "Roblox": [("greenhouse", "roblox")],
    "Databricks": [("greenhouse", "databricks")],
    "Amplitude": [("greenhouse", "amplitude")],
    "Zapier": [("greenhouse", "zapier")],
    "Airtable": [("greenhouse", "airtable")],
    "Postman": [("greenhouse", "postman")],
    "Twilio": [("greenhouse", "twilio")],
    "HubSpot": [("greenhouse", "hubspot")],
    "Cloudflare": [("greenhouse", "cloudflare")],
    "Confluent": [("greenhouse", "confluent")],
    "MongoDB": [("greenhouse", "mongodb")],
    "Okta": [("greenhouse", "okta")],
    "Datadog": [("greenhouse", "datadog")],
    "Chime": [("greenhouse", "chime")],
    "Wealthfront": [("greenhouse", "wealthfront")],
    "SoFi": [("greenhouse", "sofi")],
    "Block": [("greenhouse", "block")],
    "PayPal": [("greenhouse", "paypal")],
    "Intuit": [("greenhouse", "intuit")],
    "Adobe": [("greenhouse", "adobe")],
    "Salesforce": [("greenhouse", "salesforce")],
    "Atlassian": [("greenhouse", "atlassian")],
    "Slack": [("greenhouse", "slack")],
    "Zoom": [("greenhouse", "zoom")],
    "Peloton": [("greenhouse", "peloton")],
    "Warby Parker": [("greenhouse", "warbyparker")],
    "Faire": [("greenhouse", "faire")],
    "Whatnot": [("ashby", "whatnot")],
    "Scale AI": [("greenhouse", "scaleai")],
    "Perplexity": [("greenhouse", "perplexityai")],
    "Anthropic": [("greenhouse", "anthropic")],
    "OpenAI": [("ashby", "openai")],
    "Cursor": [("ashby", "cursor")],
    "Replit": [("ashby", "replit")],
    "Vanta": [("ashby", "vanta")],
    "Deel": [("greenhouse", "deel")],
    "Remote": [("greenhouse", "remotecom")],
    "Klarna": [("smartrecruiters", "Klarna")],
    "Booking.com": [("greenhouse", "bookingcom")],
    "Expedia Group": [("greenhouse", "expedia")],
    "Wayfair": [("greenhouse", "wayfair")],
    "Chewy": [("greenhouse", "chewy")],
    "Instacart Ads": [],
}


_verify_session = requests.Session()
_verify_session.headers.update({"User-Agent": USER_AGENT})
_PROBE_TIMEOUT = (5, 10)  # (connect, read) — a single small page, not a full paginated fetch


def verify(candidate: dict) -> bool:
    """Single lightweight request per ATS — just enough to confirm the
    token/tenant/site is real. Deliberately NOT a full paginated fetch
    (fetch_workday can mean 100+ requests for a large company's board),
    since discovery only needs a yes/no on reachability.
    """
    ats = candidate["ats"]
    try:
        if ats == "greenhouse":
            token = candidate["token"]
            resp = _verify_session.get(
                f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", timeout=_PROBE_TIMEOUT
            )
            return resp.status_code == 200
        elif ats == "ashby":
            token = candidate["token"]
            resp = _verify_session.get(
                f"https://api.ashbyhq.com/posting-api/job-board/{token}", timeout=_PROBE_TIMEOUT
            )
            return resp.status_code == 200
        elif ats == "lever":
            token = candidate["token"]
            resp = _verify_session.get(
                f"https://api.lever.co/v0/postings/{token}?mode=json&limit=1", timeout=_PROBE_TIMEOUT
            )
            return resp.status_code == 200
        elif ats == "smartrecruiters":
            token = candidate["token"]
            resp = _verify_session.get(
                f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=1",
                timeout=_PROBE_TIMEOUT,
            )
            return resp.status_code == 200
        elif ats == "workday":
            tenant, dc, site = candidate["tenant"], candidate["dc"], candidate["site"]
            url = f"https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
            body = {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}
            resp = _verify_session.post(url, json=body, timeout=_PROBE_TIMEOUT)
            if resp.status_code != 200:
                return False
            data = resp.json()
            return "jobPostings" in data
        else:
            return False
    except requests.exceptions.RequestException:
        return False
    except (ValueError, KeyError):  # bad/non-JSON response body
        return False


def verify_with_timeout(candidate: dict, timeout: float = 12.0) -> bool:
    """Run verify() with a hard wall-clock deadline.

    requests' own timeout doesn't cover OS-level DNS resolution hangs
    (observed on Windows for a couple of Workday tenants), so this wraps
    each check in its own throwaway thread: if it doesn't finish in time
    we give up and move on, leaving that one thread to leak rather than
    let it stall the entire discovery run.
    """
    # Deliberately not a context manager / shutdown() call: if the worker
    # thread is genuinely hung (e.g. a stuck DNS lookup), waiting for it to
    # exit would defeat the whole point of the timeout. We let it leak and
    # rely on os._exit() at the end of main() to skip Python's normal
    # thread-join-on-exit behavior.
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(verify, candidate)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        return False
    except Exception:  # noqa: BLE001 — any other failure means "not verified"
        return False


def main() -> None:
    all_candidates: dict[tuple[str, str], dict] = {}

    print("Pass 1: mining open-source trackers...")
    for url in README_SOURCES:
        text = fetch_text(url)
        if not text:
            print(f"  skip (unreachable): {url}")
            continue
        found = parse_readme(text)
        print(f"  {url}: {len(found)} candidate ATS links")
        all_candidates.update(found)

    print("Pass 2: adding curated PM-heavy employer list...")
    for name, guesses in KNOWN_PM_EMPLOYERS.items():
        for ats, token in guesses:
            key = (ats, token)
            if key not in all_candidates:
                all_candidates[key] = {"name": name, "ats": ats, "token": token}

    print(f"Total candidates before verification: {len(all_candidates)}")

    print("Pass 3: verifying every candidate live...")
    verified: list[dict] = []
    seen_names: set[str] = set()
    for i, candidate in enumerate(all_candidates.values(), 1):
        label = candidate.get("token") or f"{candidate.get('tenant')}/{candidate.get('dc')}/{candidate.get('site')}"
        print(f"  [{i}/{len(all_candidates)}] {candidate['ats']}:{label} ({candidate['name']}) checking...")
        ok = verify_with_timeout(candidate)
        status = "OK" if ok else "DROP"
        print(f"  [{i}/{len(all_candidates)}] {candidate['ats']}:{label} ({candidate['name']}) -> {status}")
        if ok:
            dedup_key = (candidate["name"].lower(), candidate["ats"], label)
            if dedup_key in seen_names:
                continue
            seen_names.add(dedup_key)
            verified.append(candidate)
        time.sleep(0.15)

    verified.sort(key=lambda c: c["name"].lower())
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(verified, f, sort_keys=False, allow_unicode=True)

    print(f"\nVerified {len(verified)} companies -> {OUT_PATH}")


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    sys.stderr.flush()
    import os
    os._exit(0)  # skip waiting on any leaked hung verification threads
