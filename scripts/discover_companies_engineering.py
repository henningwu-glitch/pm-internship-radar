"""Build data/companies_engineering.yaml: a VERIFIED registry of ATS
job-board APIs for the ~185 UK engineering employers on the tracked list
(Aerospace & Defence, Chemicals & Oil, Automotive, Construction &
Infrastructure, Electronics & Digital Systems, Energy & Utilities,
Multi-Sector Consultancy, Manufacturing & Product Design, Scientific
Research & Health).

Unlike scripts/discover_companies.py (the PM/UX tracker's discovery script),
this one does NOT mine community internship-tracker READMEs — those skew
almost entirely to US tech/finance employers with no relation to this
company list, and pulling them in would silently expand the tracker's scope
far beyond "these ~185 companies", which is exactly what this tracker is
scoped to. Every candidate here comes only from ENGINEERING_EMPLOYERS below:
a guess at the ATS token/tenant for each company on the list, resolved by
probing plausible guesses and keeping only what verifies with a live call.

Companies with no plausible guess at all (Civil Service bodies — MI5, MI6,
GCHQ, the Ministry of Defence, the Armed Forces, the National Crime Agency —
and small firms with no evident public ATS) are deliberately left out of the
dict rather than guessed at: an unverified/fabricated entry is worse than
one that's simply not tracked yet. See README's "Adding a company" section
to add one by hand once you've found its real token via DevTools.

Usage: python scripts/discover_companies_engineering.py
"""
from __future__ import annotations

import functools
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

import requests
import yaml

socket.setdefaulttimeout(20)
print = functools.partial(print, flush=True)  # noqa: A001

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from radar.ats_clients import USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "companies_engineering.yaml"

# {display name: [(ats, token_or_workday_tuple), ...]} — every entry is a
# GUESS. Pass 2 (verify) drops anything that doesn't resolve live, so a bad
# guess costs nothing but a dropped candidate. Grouped by the tracked list's
# own sector headings for maintainability.
ENGINEERING_EMPLOYERS: dict[str, list[tuple]] = {
    # --- Aerospace & Defence ---
    "BAE Systems": [("workday", ("baesystems", "wd3", "BAE_Systems_Careers"))],
    "Babcock": [("workday", ("babcock", "wd3", "Babcock_Careers"))],
    "Dstl": [("workday", ("dstl", "wd3", "Dstl_Careers"))],
    "GE Aerospace": [("workday", ("geaerospace", "wd5", "GE_External_Site"))],
    "Honeywell": [("workday", ("honeywell", "wd5", "Honeywell_Careers"))],
    "Leonardo": [("workday", ("leonardo", "wd3", "Leonardo_Careers"))],
    "MBDA": [("workday", ("mbda", "wd3", "MBDA_Careers"))],
    "QinetiQ": [("workday", ("qinetiq", "wd3", "QinetiQ_Careers"))],
    "Raytheon": [("workday", ("rtx", "wd1", "External"))],
    "Rolls-Royce": [("workday", ("rollsroyce", "wd3", "Rolls_Royce_Careers"))],
    "Thales": [("workday", ("thales", "wd3", "Careers"))],
    "Vertical Aerospace": [("lever", "verticalaerospace"), ("greenhouse", "verticalaerospace")],
    "Open Cosmos": [("greenhouse", "opencosmos"), ("lever", "opencosmos")],
    "Martin-Baker": [("greenhouse", "martinbaker")],
    "Subsea7": [("workday", ("subsea7", "wd3", "Subsea7_Careers"))],
    "Parker Meggitt": [("workday", ("parker", "wd1", "Parker_Careers"))],
    "European Space Agency": [("greenhouse", "esa")],
    "NATS": [("greenhouse", "nats")],
    "Royal IHC": [("greenhouse", "royalihc")],
    "AWE": [("greenhouse", "awe")],
    "Abaco": [("greenhouse", "abacosystems")],
    "BMT": [("greenhouse", "bmt")],
    # --- Chemicals & Oil ---
    "bp": [("workday", ("bp", "wd3", "bp_professionals"))],
    "Shell": [("workday", ("shell", "wd3", "SHELL_CAREERS"))],
    "ExxonMobil": [("workday", ("exxonmobil", "wd1", "ExxonMobil_Careers"))],
    "INEOS": [("greenhouse", "ineos")],
    "Johnson Matthey": [("workday", ("matthey", "wd3", "JM_Careers"))],
    "KBR": [("workday", ("kbr", "wd1", "KBR_Careers"))],
    "Petrofac": [("workday", ("petrofac", "wd3", "Petrofac_Careers"))],
    "Centrica": [("workday", ("centrica", "wd3", "Centrica_Careers"))],
    "Fugro": [("workday", ("fugro", "wd3", "Careers"))],
    "Sulzer": [("workday", ("sulzer", "wd3", "Sulzer_Careers"))],
    "Fluor": [("workday", ("fluor", "wd1", "Fluor_Careers"))],
    "Oceaneering": [("workday", ("oceaneering", "wd1", "Oceaneering_Careers"))],
    "Viridien": [("greenhouse", "viridien")],
    # --- Automotive ---
    "Aston Martin": [("workday", ("astonmartin", "wd3", "Aston_Martin_Careers"))],
    "Aston Martin F1": [("greenhouse", "astonmartinf1")],
    "Bentley": [("workday", ("bentley", "wd3", "Bentley_Careers"))],
    "McLaren Automotive": [("greenhouse", "mclarenautomotive"), ("workday", ("mclaren", "wd3", "McLaren_Careers"))],
    "Nissan": [("workday", ("nissan", "wd3", "Nissan_Careers"))],
    "Quick Release (Automotive)": [("greenhouse", "quickrelease")],
    # --- Construction & Infrastructure ---
    "Arcadis": [("workday", ("arcadis", "wd3", "Arcadis_Careers"))],
    "Arup": [("greenhouse", "arup"), ("workday", ("arup", "wd3", "Arup_Careers"))],
    "AtkinsRéalis": [("workday", ("atkinsrealis", "wd3", "AtkinsRealis_Careers"))],
    "Balfour Beatty": [("workday", ("balfourbeatty", "wd3", "Balfour_Beatty_Careers"))],
    "Bechtel": [("workday", ("bechtel", "wd1", "Bechtel_Careers"))],
    "Buro Happold": [("greenhouse", "burohappold")],
    "Costain": [("greenhouse", "costain")],
    "Foster + Partners": [("greenhouse", "fosterandpartners")],
    "Galliford Try": [("greenhouse", "gallifordtry")],
    "Kier Group": [("workday", ("kier", "wd3", "Kier_Careers"))],
    "Laing O'Rourke": [("workday", ("laingorourke", "wd3", "LOR_Careers"))],
    "Mace Construct": [("greenhouse", "mace"), ("workday", ("mace", "wd3", "Mace_Careers"))],
    "Mace Consult": [("greenhouse", "mace")],
    "Mott MacDonald": [("workday", ("mottmac", "wd3", "MottMac_Careers"))],
    "National Highways": [("greenhouse", "nationalhighways")],
    "Network Rail": [("workday", ("networkrail", "wd3", "Network_Rail_Careers"))],
    "Severfield": [("greenhouse", "severfield")],
    "Tarmac": [("workday", ("tarmac", "wd3", "Tarmac_Careers"))],
    "Transport for London": [("workday", ("tfl", "wd3", "TfL_Careers"))],
    "Cundall": [("greenhouse", "cundall")],
    "Genuit Group": [("greenhouse", "genuitgroup")],
    "Robertson Group": [("greenhouse", "robertsongroup")],
    "Sisk": [("greenhouse", "johnsisk")],
    "Tetra Tech": [("workday", ("tetratech", "wd1", "Tetra_Tech_Careers"))],
    "Thornton Tomasetti": [("greenhouse", "thorntontomasetti")],
    "Tilbury Douglas": [("greenhouse", "tilburydouglas")],
    "Burns & McDonnell": [("workday", ("burnsmcd", "wd1", "BurnsMcDonnell_Careers"))],
    # --- Electronics & Digital Systems ---
    "Analog Devices": [("workday", ("analog", "wd1", "ADI_Careers"))],
    "Arm": [("workday", ("arm", "wd3", "Arm_Careers"))],
    "Cambridge Consultants": [("greenhouse", "cambridgeconsultants")],
    "Capgemini Engineering": [("workday", ("capgemini", "wd3", "Capgemini_Careers"))],
    "Cirrus Logic": [("greenhouse", "cirruslogic")],
    "Graphcore": [("greenhouse", "graphcore")],
    "Imagination Technologies": [("greenhouse", "imaginationtech")],
    "Intel": [("workday", ("intel", "wd1", "External"))],
    "Keysight Technologies": [("workday", ("keysight", "wd1", "Keysight_Careers"))],
    "PA Consulting Group": [("greenhouse", "paconsulting")],
    "Sky": [("smartrecruiters", "Sky")],
    "Virgin Media O2": [("workday", ("vmo2", "wd3", "VMO2_Careers"))],
    "Frazer-Nash Consultancy": [("greenhouse", "frazernash")],
    "Fibrus": [("greenhouse", "fibrus")],
    "Expedera": [("greenhouse", "expedera")],
    "TUV SUD": [("workday", ("tuvsud", "wd3", "TUVSUD_Careers"))],
    # --- Energy & Utilities ---
    "EDF": [("greenhouse", "edfenergy")],
    "Eaton": [("workday", ("eaton", "wd1", "EatonCareers"))],
    "GE Vernova": [("workday", ("gevernova", "wd5", "GE_External_Site"))],
    "RWE": [("workday", ("rwe", "wd3", "RWE_Careers"))],
    "SLB": [("workday", ("slb", "wd3", "SLB_Careers"))],
    "SSE": [("greenhouse", "sse")],
    "Schneider Electric": [("workday", ("schneiderelectric", "wd3", "SE_Careers"))],
    "ScottishPower": [("workday", ("scottishpower", "wd3", "ScottishPower_Careers"))],
    "Sellafield Ltd": [("greenhouse", "sellafieldltd")],
    "Severn Trent": [("greenhouse", "severntrent")],
    "Thames Water": [("greenhouse", "thameswater")],
    "United Utilities": [("greenhouse", "unitedutilities")],
    "Veolia UK": [("workday", ("veolia", "wd3", "Veolia_Careers"))],
    "Yorkshire Water": [("greenhouse", "yorkshirewater")],
    "Assystem": [("greenhouse", "assystem")],
    "Seaway7": [("greenhouse", "seaway7")],
    "UK Atomic Energy Authority": [("greenhouse", "ukaea")],
    "Sizewell C": [("greenhouse", "sizewellc")],
    # --- Multi-Sector Consultancy ---
    "AECOM": [("workday", ("aecom", "wd1", "AECOM_Careers"))],
    "AFRY": [("smartrecruiters", "AFRY")],
    "Amentum": [("workday", ("amentum", "wd1", "Amentum_Careers"))],
    "Capgemini": [("workday", ("capgemini", "wd3", "Capgemini_Careers"))],
    "DNV": [("workday", ("dnv", "wd3", "DNV_Careers"))],
    "Jacobs": [("workday", ("jacobs", "wd3", "External_Careers"))],
    "Ramboll": [("greenhouse", "ramboll")],
    "RINA Consulting": [("greenhouse", "rina")],
    "Turner & Townsend": [("smartrecruiters", "TurnerTownsend")],
    "WSP": [("workday", ("wsp", "wd3", "WSP_Careers"))],
    "Wood": [("workday", ("wood", "wd3", "Wood_Careers"))],
    "Haskoning": [("greenhouse", "royalhaskoningdhv")],
    "Osprey Group": [("greenhouse", "ospreygroup")],
    "Risktec Solutions": [("greenhouse", "risktec")],
    "TotalSim CFD": [("greenhouse", "totalsim")],
    # --- Manufacturing & Product Design ---
    "3M": [("workday", ("3m", "wd1", "Search"))],
    "ABB": [("workday", ("abb", "wd3", "abbcareers"))],
    "Bosch": [("smartrecruiters", "BoschGroup")],
    "British American Tobacco": [("greenhouse", "bat")],
    "Cargill": [("workday", ("cargill", "wd1", "Cargill_External_Career_Site"))],
    "Caterpillar": [("workday", ("caterpillar", "wd1", "Caterpillar_Careers"))],
    "Diageo": [("workday", ("diageo", "wd3", "Diageo_Careers"))],
    "Dyson": [("greenhouse", "dyson"), ("workday", ("dyson", "wd3", "Dyson_Careers"))],
    "Edwards": [("greenhouse", "edwardsvacuum")],
    "Essity": [("workday", ("essity", "wd3", "Essity_Careers"))],
    "Procter & Gamble": [("workday", ("pg", "wd5", "PG_Careers"))],
    "Renishaw": [("greenhouse", "renishaw")],
    "Siemens": [("workday", ("siemens", "wd3", "Siemens_Internal"))],
    "ASMPT": [("greenhouse", "asmpt")],
    "Alloyed": [("greenhouse", "alloyed")],
    "Fortescue": [("greenhouse", "fortescue")],
    "Isembard": [("greenhouse", "isembard")],
    "Labman": [("greenhouse", "labman")],
    "MTC": [("greenhouse", "the-mtc")],
    "Oshkosh": [("workday", ("oshkosh", "wd1", "Oshkosh_Careers"))],
    # --- Scientific Research & Health ---
    "GSK": [("workday", ("gsk", "wd3", "GSK_Careers"))],
    "Roke": [("greenhouse", "roke")],
    "Siemens Healthineers": [("workday", ("siemenshealthineers", "wd3", "SHS_Careers"))],
    "UK National Nuclear Laboratory": [("greenhouse", "uknnl")],
    "Canon Medical Research Europe": [("greenhouse", "canonmedicalresearch")],
    "Science & Technology Facilities Council": [("greenhouse", "stfc")],
}


_verify_session = requests.Session()
_verify_session.headers.update({"User-Agent": USER_AGENT})
_PROBE_TIMEOUT = (5, 10)


def verify(candidate: dict) -> bool:
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
            # The postings API (.../v1/companies/{token}/postings) returns
            # HTTP 200 with an empty result set for ANY token, real or not —
            # useless as a verification signal on its own. Two checks
            # together are needed: (1) the public jobs redirect, which
            # discriminates a real token (redirects to
            # careers.smartrecruiters.com/{token}, or the company's own
            # white-labeled domain) from an invalid one (bounces back to the
            # generic jobs.smartrecruiters.com landing page); and (2) the
            # postings API actually reporting totalFound > 0, since several
            # large employers hold a reserved/placeholder SmartRecruiters
            # company profile with zero published postings behind it —
            # recognized by (1) but not a live board by any useful measure.
            token = candidate["token"]
            resp = _verify_session.get(
                f"https://jobs.smartrecruiters.com/{token}", timeout=_PROBE_TIMEOUT
            )
            if resp.status_code != 200 or resp.url.rstrip("/") == "https://jobs.smartrecruiters.com":
                return False
            resp2 = _verify_session.get(
                f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=1",
                timeout=_PROBE_TIMEOUT,
            )
            return resp2.status_code == 200 and resp2.json().get("totalFound", 0) > 0
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
    except (ValueError, KeyError):
        return False


def verify_with_timeout(candidate: dict, timeout: float = 12.0) -> bool:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(verify, candidate)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        return False
    except Exception:  # noqa: BLE001
        return False


def main() -> None:
    all_candidates: dict[tuple[str, str], dict] = {}

    print("Resolving candidates from the curated engineering employer list...")
    for name, guesses in ENGINEERING_EMPLOYERS.items():
        for ats, token in guesses:
            if ats == "workday":
                tenant, dc, site = token
                key = ("workday", f"{tenant}/{dc}/{site}")
                if key not in all_candidates:
                    all_candidates[key] = {"name": name, "ats": "workday", "tenant": tenant, "dc": dc, "site": site}
            else:
                key = (ats, token)
                if key not in all_candidates:
                    all_candidates[key] = {"name": name, "ats": ats, "token": token}

    print(f"Total candidates before verification: {len(all_candidates)} (from {len(ENGINEERING_EMPLOYERS)} companies)")

    print("Verifying every candidate live...")
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

    print(
        f"\nVerified {len(verified)} of {len(ENGINEERING_EMPLOYERS)} companies "
        f"-> {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    sys.stderr.flush()
    import os
    os._exit(0)
