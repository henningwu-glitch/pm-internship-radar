# PM Internship Radar — Summer 2027

Tracks Product Manager (including APM / Technical PM) internships for the
Summer 2027 cycle by polling company ATS boards directly — Greenhouse,
Ashby, Lever, Workday, SmartRecruiters — twice a day. No LinkedIn/Indeed
scraping (both prohibit it, and neither is the original source anyway).

## How it works

1. **`data/companies.yaml`** — a verified registry of companies and their
   ATS token/tenant. Every entry was confirmed live before being added; a
   wrong token 404s instead of silently returning nothing, so nothing here
   is guessed.
2. **`scripts/poll.py`** — calls each company's public job-board API,
   classifies postings for PM relevance (`radar/classify.py`), and merges
   results into `data/postings.json` (`radar/storage.py`). A posting's
   `first_seen_at` is stamped by our own clock the first time we see it and
   is never rewritten — that's the only definition of "new" this project
   trusts.
3. **`scripts/build_site.py`** — renders `data/postings.json` into a static
   `site/index.html` (vanilla JS, no server, no build step).
4. **`.github/workflows/tracker.yml`** — runs the poll + build twice daily,
   commits the updated data, and redeploys the site to GitHub Pages.

## Local development

```bash
python -m venv .venv
.venv/Scripts/activate   # or: source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

pytest tests/                        # zero network calls
python scripts/discover_companies.py # rebuild data/companies.yaml (verifies live)
python scripts/poll.py               # poll every company, update data/postings.json
python scripts/build_site.py         # render site/index.html
```

Open `site/index.html` directly in a browser to preview.

## Adding a company

Add a verified entry to `data/companies.yaml`:

```yaml
- name: Example Corp
  ats: greenhouse   # or: ashby, lever, smartrecruiters, workday
  token: examplecorp
```

Workday entries need `tenant`, `dc`, and `site` instead of `token` — find
them via DevTools → Network tab on the company's live careers page (the
request URL contains all three: `https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`).

Never add an entry you haven't personally verified returns real data —
run `python scripts/discover_companies.py` to re-verify the whole registry,
or test one company directly with `radar/ats_clients.py`.

## Why an empty board is sometimes correct

Most companies don't open Summer 2027 postings until November–February. If
`data/postings.json` is empty or thin, the site says so honestly rather
than fabricating anything.
