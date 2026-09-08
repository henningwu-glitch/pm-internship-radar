# UK Internship Radar — Summer 2027

Two trackers sharing one polling engine — both **based in the UK**, both
polling company ATS boards directly (Greenhouse, Ashby, Lever, Workday,
SmartRecruiters, Teamtailor), no LinkedIn/Indeed scraping (both prohibit it,
and neither is the original source anyway):

- **PM/UX Radar** (`site/index.html`) — Product Manager, Product Owner, and
  UX/product-design internships, at a broad, self-expanding company registry
  mined from open-source internship trackers plus a curated PM-heavy list.
  Updates three times daily at 06:00 / 14:00 / 22:00 UTC.
- **Engineering Radar** (`site/engineering.html`) — any Summer 2027
  internship/placement (engineering, commercial analyst, whatever the
  discipline) at a curated, fixed list of ~185 UK engineering, defence,
  construction, energy, and manufacturing employers. No role-keyword
  filtering — the company list itself is what scopes it to engineering
  employers. Updates three times daily at 9am / 12pm / 2pm **UK local
  time**.

## PM/UX Radar

A posting only survives if it matches on **both** title (PM/APM/Technical
PM, Product Owner, or UX/product-design internship, Summer 2027 or
unspecified year — see `radar/classify.py::ROLE_PATTERNS`) and
**location** (UK country/nation name, or an unambiguous UK city — see
`is_uk_location`). The company registry itself is not UK-only — several
large global employers with UK offices are included — but only their
UK-located postings pass the filter.

## How it works

1. **`scripts/discover_companies.py`** — rebuilds `data/companies.yaml`
   from scratch on every run: mines ATS links out of community-maintained
   internship trackers (SimplifyJobs, vanshb03, zshah101 — these are
   updated by their communities daily, which is how new employers get
   picked up automatically without a paid search API), adds a curated list
   of known product/design employers, then verifies every single candidate
   with a live call before keeping it. A wrong token 404s instead of
   silently returning nothing, so nothing in the registry is guessed, and
   a company that goes dark drops out on its own.
2. **`scripts/poll.py`** — calls each company's public job-board API,
   classifies postings for role + UK-location relevance
   (`radar/classify.py`), and merges results into `data/postings.json`
   (`radar/storage.py`). A posting's `first_seen_at` is stamped by our own
   clock the first time we see it and is never rewritten — that's the only
   definition of "new" this project trusts.
3. **`scripts/build_site.py`** — renders `data/postings.json` into a static
   `site/index.html` (vanilla JS, no server, no build step).
4. **`.github/workflows/tracker.yml`** — runs discovery + poll + build
   three times daily (06:00 / 14:00 / 22:00 UTC), commits the updated data,
   and redeploys the site to GitHub Pages.

## Engineering Radar

Unlike the PM tracker, this one doesn't filter by role/title keyword at
all — see `radar/classify_engineering.py`. The company registry
(`data/companies_engineering.yaml`) is itself a curated, fixed list of ~185
UK engineering employers, so any Summer 2027 internship/placement any of
them posts is in scope. A posting still needs a placement-shaped title
("Internship", "Placement", "Year in Industry", "Vacation Scheme", ...), the
2027 cycle (or no year at all), and a UK location.

1. **`scripts/discover_companies_engineering.py`** — resolves each of the
   ~185 companies to its ATS token/tenant by probing plausible guesses, then
   verifies every candidate with a live call — same honest philosophy as the
   PM tracker's discovery script, but scoped only to this fixed employer
   list (it does **not** mine the community trackers, which skew almost
   entirely US tech/finance and would silently expand scope far beyond
   these ~185 companies).
2. **`scripts/poll_engineering.py`** / **`scripts/build_site_engineering.py`**
   — same shape as the PM tracker's, writing to `data/postings_engineering.json`
   and `site/engineering.html`.
3. **`.github/workflows/tracker-engineering.yml`** — runs three times daily
   at 9am / 12pm / 2pm **UK local time** (two cron schedules approximate UK
   clock time across the BST/GMT switch, since GitHub Actions cron is
   UTC-only).

Most large UK industrials (defence primes, utilities, construction) run
entirely bespoke careers platforms — Phenom People, Sitecore+Coveo/Solr,
SuccessFactors, Oracle Taleo — with no public JSON API to poll at all, not
just an unguessable token; some are actively hardened against automated
access (Cloudflare bot challenges). Coverage of the ~185-company list is
necessarily partial as a result — a company that doesn't verify simply
isn't polled, rather than shown with a guessed link. Run the discovery
script to see the current verified count; add a company by hand once
you've found its real token (see "Adding a company" below).

The engineering site also has a **"My status"** column (Not Applied /
Applied / Interviewing / Offer / Rejected) you can click through per
posting — stored only in your own browser's `localStorage`, never sent
anywhere, so it works like a personal application tracker layered on top of
the live feed.

## Local development

```bash
python -m venv .venv
.venv/Scripts/activate   # or: source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

pytest tests/                                    # zero network calls

# PM/UX tracker
python scripts/discover_companies.py             # rebuild data/companies.yaml (verifies live)
python scripts/poll.py                           # poll every company, update data/postings.json
python scripts/build_site.py                     # render site/index.html

# Engineering tracker
python scripts/discover_companies_engineering.py # rebuild data/companies_engineering.yaml (verifies live)
python scripts/poll_engineering.py               # poll every company, update data/postings_engineering.json
python scripts/build_site_engineering.py         # render site/engineering.html
```

Open `site/index.html` or `site/engineering.html` directly in a browser to preview.

## Adding a company

Add a verified entry to `data/companies.yaml` (PM tracker) or
`data/companies_engineering.yaml` (Engineering tracker):

```yaml
- name: Example Corp
  ats: greenhouse   # or: ashby, lever, smartrecruiters, teamtailor, workday
  token: examplecorp
```

Workday entries need `tenant`, `dc`, and `site` instead of `token` — find
them via DevTools → Network tab on the company's live careers page (the
request URL contains all three: `https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`).

Teamtailor entries need `domain` instead of `token` — the company's careers
hostname itself (either their default `{company}.teamtailor.com` or a
white-labeled custom domain like `careers.example.com`); confirm it works
by checking `https://{domain}/jobs.json` returns a JSON Feed with an
`items` array.

Never add an entry you haven't personally verified returns real data —
re-run the relevant discovery script to re-verify the whole registry, or
test one company directly with `radar/ats_clients.py`. For the Engineering
tracker specifically, also add the company to `ENGINEERING_EMPLOYERS` in
`scripts/discover_companies_engineering.py` so it survives the next
automated re-discovery run instead of being silently dropped.

## Why an empty board is sometimes correct

Most companies don't open Summer 2027 postings until November–February. If
a postings file is empty or thin, the site says so honestly rather than
fabricating anything.
