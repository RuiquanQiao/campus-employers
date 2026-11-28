"""Look for a graduate or intern posting on the employer's own recruiting system, with no AI and no web search.

    python scripts/ats_check.py <cc> [--detect] [--limit N]

For each employer whose latest check line (dist/checks/<cc>-*.out.jsonl) is not `confirmed`, its careers
addresses (campus_site, site_candidates, the page the check read) are handed to career-ops' job providers, the
ones Resume Studio's scan uses (Workday, Greenhouse, Lever, Ashby, SmartRecruiters, Oracle, SuccessFactors and
some 150 more; `jobs/co_scan.mjs` in a Resume Studio checkout beside this one). They read the system's public job
API, which a page fetch cannot (Workday's pages are drawn by scripts and come back empty).

A posting counts when its title names a graduate, intern, vacation, cadet, co-op, summer analyst or new-grad role
and its location is in the country. Such employers are written to dist/checks/<cc>-ats.out.jsonl as `confirmed`,
with the posting as `programme` and its title and location as `evidence`, in the format of CHECK_BRIEF.md; a
system that answered with no such posting is written as nothing (the check's line stays). --detect only prints
which provider each address resolves to.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RS = ROOT.parent / "resume-studio"
BRIDGE = RS / "jobs" / "co_scan.mjs"
PROVIDERS = RS / "jobs" / "vendor" / "career-ops"
OUT = ROOT / "dist" / "checks"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import latest  # noqa: E402

# a programme for students or new graduates; apprentices, trade trainees and campus staff are not one
GRAD = re.compile(r"\b(intern(ship)?s?|graduate|grad\b|new[- ]grad|vacation(er)?|vacation (program|student)|"
                  r"cadet(ship)?|co-?op\b|summer (analyst|associate|scholar)|early[- ]careers?|"
                  r"university (hire|graduate|program))\b", re.I)
# a senior role that names graduates only in passing ("Graduate Recruitment Manager") is not an intake, nor is a
# university's own staff role ("Dean of Students", "Graduate School Coordinator") or an event
NOT_INTAKE = re.compile(r"\b(manager|lead|director|head of|recruiter|coordinator|advisor|partner|specialist|"
                        r"senior|principal|professor|lecturer|teacher|nurse educator|dean|graduate school|"
                        r"graduate (admissions|studies|research assistant|assistant)|career fair|showcase|"
                        r"postdoc|fellow\b|expo\b|fair\b|info(rmation)? session|webinar|"
                        r"\b20(0\d|1\d|2[0-4])\b)", re.I)   # an event, or a posting left up from 2024 or before
GRAD_KIND = re.compile(r"\b(graduate|grad\b|new[- ]grad|university|early[- ]careers?|cadet)|新卒|trainee|absolvent|"
                       r"berufseinst|direkteinstieg|graduate scheme", re.I)
# a location in another country, which a state code would otherwise match ("Seattle, WA, United States" for
# Australia; "Calgary, AB, CA", "Mumbai, IN", "München, DE" for the United States)
ABROAD = {
    "au": re.compile(r"united states|\bUSA?\b|canada|united kingdom|\bUK\b|india|singapore|new zealand|"
                     r"south africa|johannesburg|cape town|philippines|malaysia|ireland|germany", re.I),
    # "San Jose, CA" and "Indianapolis, IN" are American: a code counts as a country only after a province
    # ("Calgary, AB, CA") or with the place named
    "us": re.compile(r"canada|\b(AB|BC|ON|QC|MB|SK|NS),\s*CA\b|india\b|mumbai|bengaluru|bangalore|pune|hyderabad|"
                     r"chennai|germany|deutschland|m[üu]nchen|munich|berlin|united kingdom|\bUK\b|london|toronto|"
                     r"calgary|vancouver|montr[ée]al|mexico|australia|sydney|singapore|ireland|dublin|philippines|"
                     r"manila|china|shanghai|japan|tokyo|brazil|poland|netherlands|france|paris|israel", re.I),
}
AU_PLACE = re.compile(r"\b(australia|aus\b|sydney|melbourne|brisbane|perth|adelaide|canberra|hobart|darwin|"
                      r"gold coast|newcastle|wollongong|geelong|townsville|cairns|parramatta|north sydney|"
                      r"nsw|vic\b|qld|wa\b|sa\b|act\b|tas\b|nt\b|new south wales|victoria|queensland|"
                      r"western australia|south australia|tasmania|northern territory)\b", re.I)
US_STATES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC "
             "ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split()
US_CODE = re.compile(r"(^|[\s,(\-])(" + "|".join(US_STATES) + r"|US|USA)([\s,)\-]|$)")   # "Chicago, IL"
US_PLACE = re.compile(r"\b(united states|usa|u\.s\.|alabama|alaska|arizona|"
                      r"california|colorado|connecticut|florida|georgia|illinois|indiana|massachusetts|michigan|"
                      r"minnesota|new jersey|new york|north carolina|ohio|oregon|pennsylvania|texas|virginia|"
                      r"washington|wisconsin|tennessee|missouri|maryland|kentucky|louisiana|utah|iowa|kansas|"
                      r"nevada|oklahoma|arkansas|nebraska|idaho|delaware|chicago|boston|seattle|houston|dallas|"
                      r"atlanta|austin|denver|san francisco|los angeles|new york city|nyc|remote - us|us remote)\b",
                      re.I)
GB_PLACE = re.compile(r"\b(united kingdom|uk|great britain|england|scotland|wales|northern ireland|london|manchester|"
                      r"birmingham|leeds|glasgow|edinburgh|bristol|cardiff|belfast|cambridge|oxford|reading|"
                      r"newcastle|liverpool|sheffield|nottingham|leicester|southampton|aberdeen|milton keynes|"
                      r"coventry|derby|bath|guildford|warrington|swindon|brighton|york|norwich|ipswich|exeter)\b", re.I)
JP_PLACE = re.compile(r"japan|日本|tokyo|東京|osaka|大阪|nagoya|名古屋|yokohama|横浜|kyoto|京都|kobe|神戸|fukuoka|福岡|"
                      r"sapporo|札幌|sendai|仙台|hiroshima|広島|kawasaki|川崎|saitama|埼玉|chiba|千葉|都|道|府|県", re.I)
DE_PLACE = re.compile(r"\b(germany|deutschland|berlin|munich|münchen|muenchen|hamburg|frankfurt|cologne|köln|koeln|"
                      r"stuttgart|düsseldorf|duesseldorf|dortmund|essen|leipzig|dresden|hannover|hanover|nuremberg|"
                      r"nürnberg|bremen|bonn|mannheim|karlsruhe|wiesbaden|mainz|aachen|heidelberg|ingolstadt|"
                      r"wolfsburg|erlangen|darmstadt|regensburg|ulm|walldorf|jena|kiel|freiburg|augsburg|potsdam)\b",
                      re.I)
PLACES = {"au": AU_PLACE, "us": US_PLACE, "gb": GB_PLACE, "jp": JP_PLACE, "de": DE_PLACE}
# titles in Japanese and German: 新卒 / インターン; Trainee, Praktikum, Werkstudent, Absolvent, Berufseinstieg
GRAD_LOCAL = re.compile(r"新卒|インターン|第二新卒|praktik|werkstudent|trainee|absolvent|berufseinst|"
                        r"direkteinstieg|abschlussarbeit|masterarbeit|bachelorarbeit|graduate scheme|placement year|"
                        r"industrial placement|spring week", re.I)
# addresses a provider would read as another employer's or as no employer's list
SKIP = re.compile(r"linkedin\.com|seek\.com|indeed\.|glassdoor|gradconnection|prosple|handshake", re.I)
ATS_HOST = re.compile(r"myworkdayjobs|pageuppeople|successfactors|oraclecloud|taleo|greenhouse|lever\.co|avature|"
                      r"eightfold|smartrecruiters|icims|workable|ashbyhq|brassring|jobvite|ultipro|ukg|paylocity|"
                      r"adp\.com|csod|teamtailor|recruitee|bamboohr|rippling|jazzhr|applicantpro|neogov|"
                      r"governmentjobs|hibob|pinpointhq|breezy|dayforce", re.I)


def addresses(rec: dict, line: dict, opened: list[str]) -> list[str]:
    urls = [rec.get("campus_site") or "", *(rec.get("site_candidates") or []), line.get("programme") or "", *opened]
    return [u for u in dict.fromkeys(u.strip() for u in urls) if u.startswith("http") and not SKIP.search(u)]


def pages_opened(cc: str) -> dict[str, list[str]]:
    """The recruiting-system pages grad_pages.py opened for each employer (dist/checks/<cc>-NN.pages.jsonl)."""
    out: dict[str, list[str]] = {}
    for f in sorted(OUT.glob(f"{cc}-*.pages.jsonl")):
        for x in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(x)
            except json.JSONDecodeError:
                continue
            urls = [p.get("url") or "" for p in r.get("pages") or []]
            out.setdefault(r.get("name", ""), []).extend(u for u in urls if ATS_HOST.search(u))
    return out


def run_bridge(entries: list[dict], detect: bool, timeout: int) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8",
                                     dir=ROOT / "dist") as f:
        json.dump({"entries": entries}, f)
        tmp = Path(f.name)
    try:
        args = [shutil.which("node") or "node", str(BRIDGE), str(PROVIDERS), str(tmp)] + (["--detect"] if detect else [])
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        out = p.stdout.strip().splitlines()
        return json.loads(out[-1])["results"] if out else []
    except (subprocess.TimeoutExpired, json.JSONDecodeError, IndexError):
        return []
    finally:
        tmp.unlink(missing_ok=True)


def place_ok(cc: str, loc: str, url: str) -> bool:
    if cc in ABROAD and ABROAD[cc].search(loc):
        return False
    if cc == "us":   # state codes are upper case ("Chicago, IL"); words in any case
        return bool(US_PLACE.search(loc) or US_CODE.search(loc))
    if cc in ("gb", "jp", "de"):
        return bool(PLACES[cc].search(loc))
    return bool(AU_PLACE.search(loc) or (not loc and re.search(r"\.com\.au|/en-au|australia", url, re.I)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cc", choices=sorted(PLACES))
    ap.add_argument("--detect", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--again", action="store_true", help="filter the lists read last time instead of reading them")
    a = ap.parse_args()
    # this script's own earlier lines are not the check's: they would hide the employers they confirmed
    results = latest(a.cc, skip=f"{a.cc}-ats.out.jsonl")
    recs = {r["name"]: r for r in json.loads((ROOT / "dist" / f"{a.cc}.json").read_text(encoding="utf-8"))}
    todo = [(n, recs[n], line) for n, line in results.items()
            if n in recs and line.get("status") != "confirmed"]
    opened = pages_opened(a.cc)
    entries = [{"key": f"{n}\x1f{j}", "name": n, "url": u}
               for i, (n, rec, line) in enumerate(todo)
               for j, u in enumerate(addresses(rec, line, opened.get(n, [])))]
    # detect is cheap (no request): one call
    found = {r["key"]: r["provider"] for r in run_bridge(entries, True, 300) if r.get("provider")}
    print(f"{a.cc}: {len(todo)} employers not confirmed, {len(entries)} addresses, {len(found)} on a known system: "
          f"{dict(Counter(found.values()).most_common(25))}")
    if a.detect:
        return 0
    # one address per employer per system is enough
    picked, seen = [], set()
    for e in entries:
        if e["key"] in found and (e["name"], found[e["key"]]) not in seen:
            seen.add((e["name"], found[e["key"]]))
            picked.append({**e, "timeout_ms": 25000, "tries": 2, "waits_ms": [3000]})
    if a.limit:
        picked = picked[:a.limit]
    raw = ROOT / ".cache" / f"{a.cc}-ats.raw.json"   # the lists as read, so the rules can be changed without asking again
    if a.again and raw.is_file():
        got = json.loads(raw.read_text(encoding="utf-8"))
    else:
        chunks = [picked[i:i + 8] for i in range(0, len(picked), 8)]
        got = []
        with ThreadPoolExecutor(6) as pool:
            for k, res in enumerate(pool.map(lambda c: run_bridge(c, False, 600), chunks), 1):
                got += res
                if k % 10 == 0:
                    print(f"  {k}/{len(chunks)} groups read", flush=True)
        raw.parent.mkdir(exist_ok=True)
        raw.write_text(json.dumps(got, ensure_ascii=False), encoding="utf-8")
    # a list several employers point to (a parent's, a fund manager's) can't say which of them hires: none is taken
    users = Counter(r["url"] for r in got if "jobs" in r)
    shared = {u for u, k in users.items() if k > 1}
    names = {n for n, _, _ in todo}
    lines: dict[str, dict] = {}
    read = errors = 0
    for r in got:
        if r["url"] in shared:
            continue
        # keyed by name: a refilter (--again) may run against a different list of employers
        name = r["key"].rsplit("\x1f", 1)[0]
        if name not in names:
            continue
        if "jobs" not in r:
            errors += 1
            continue
        read += 1
        hits = [j for j in r["jobs"] if (GRAD.search(j["title"]) or (a.cc in ("gb", "jp", "de") and GRAD_LOCAL.search(j["title"]))) and not NOT_INTAKE.search(j["title"])
                and place_ok(a.cc, j["location"], j["url"])]
        if not hits or name in lines:
            continue
        best = sorted(hits, key=lambda j: not GRAD_KIND.search(j["title"]))[0]
        hires = sorted({"graduate" if GRAD_KIND.search(j["title"]) else "internship" for j in hits})
        lines[name] = {"name": name, "status": "confirmed", "programme": best["url"], "hires": hires, "notes": "",
                       "evidence": f'{best["title"]} ({best["location"] or "no location given"}), '
                                   f'{len(hits)} such posting(s) on {r["provider"]}', "source": "ats"}
    order = [n for n, _, _ in todo if n in lines]
    (OUT / f"{a.cc}-ats.out.jsonl").write_text("".join(json.dumps(lines[n], ensure_ascii=False) + "\n" for n in order),
                                               encoding="utf-8")
    for u in sorted(shared):
        print(f"  shared list, not taken: {u} ({', '.join(r['key'].rsplit(chr(31), 1)[0] for r in got if r['url'] == u)})")
    print(f"{a.cc}: {len(picked)} lists asked, {read} read, {errors} failed; {len(lines)} employers with a graduate "
          f"or intern posting in the country -> dist/checks/{a.cc}-ats.out.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
