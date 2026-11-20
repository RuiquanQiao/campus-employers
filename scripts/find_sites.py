"""Find each employer's careers site from its homepage, and the recruiting system behind it. No AI, no search.

    python scripts/find_sites.py [--sector banks] [--limit 50] [--dry] [--studio E:/Forge/resume-studio]

For every line with a `website` and no `campus_site`:
1. its homepage is opened and its links read; the ones that lead to recruiting (a recruiting system's address, or a
   link named 校园招聘 / 招聘 / 加入我们 / careers …) are followed one step further, the same way;
2. the addresses found are ranked (a recruiting system's address that is a campus page first) and kept, best first,
   in `site_candidates`;
3. each candidate is then asked, in that order, which system runs it: by its address (zhiye.com is 北森 …), and, when
   Resume Studio is beside this repository (or named with --studio), by Resume Studio's own detectors, the same ones
   its scan uses (北森 / HotJob / 飞书 / 国聘 / 阿里系 on any domain). The first that a detector reads, or failing
   that the first whose page names the employer, becomes `campus_site` with `system` and `checked` set.

What was tried for each employer goes to dist/find-report.tsv. Files are rewritten in place, one line per employer.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_sites import fetch, names, verdict  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# a recruiting system's address: (host pattern, system's name)
SYSTEMS = [
    (r"(^|\.)zhiye\.com$", "北森"),
    (r"(^|\.)mokahr\.com$", "Moka"),
    (r"(^|\.)hotjob\.cn$", "HotJob"),
    (r"(^|\.)jobs\.feishu\.cn$|(^|\.)f\.mioffice\.cn$", "飞书"),
    (r"(^|\.)iguopin\.com$", "国聘"),
    (r"^(xiaoyuan|campus)\.zhaopin\.com$", "智联"),
    (r"^campus\.51job\.com$|^jobs\.51job\.com$", "前程无忧"),
    (r"(^|\.)dajie\.com$", "大街"),
]
CAMPUS = re.compile(r"校园招聘|校招|应届|毕业生|campus|graduate|xiaoyuan|school|students?", re.I)
CAREERS = re.compile(r"招聘|加入我们|加入.{0,4}(我们|团队)|人才(招聘|发展|中心)|^人才$|职位|岗位|join\s*us|careers?|jobs?\b|recruit", re.I)
CAREER_URL = re.compile(r"career|job|zhaopin|recruit|campus|talent|joinus|join-us|/hr\b|^https?://hr\.|xiaoyuan", re.I)
ANCHOR = re.compile(r"<a\b[^>]*?href\s*=\s*[\"']([^\"'#][^\"']*)[\"'][^>]*>(.*?)</a>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
RAW = re.compile(r"https?://[\w.-]+\.(?:zhiye\.com|mokahr\.com|hotjob\.cn|jobs\.feishu\.cn|iguopin\.com)[^\s\"'<>]*", re.I)
BOT = re.compile(r"EO_Bot|acw_sc__v2|__jsl_clearance|_0x[0-9a-f]{4}|document\.cookie\s*=|location\.href\s*=", re.I)
ABROAD = re.compile(r"^/(au|us|uk|en|en-\w+|global|int|intl|eu|de|fr|jp|sg|my|th|br|mx)(/|$)", re.I)
SKIP = re.compile(r"\.(pdf|docx?|xlsx?|jpg|png|gif|zip|rar)$|^(mailto|javascript|tel):", re.I)


def system_of(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return next((name for pat, name in SYSTEMS if re.search(pat, host)), "")


def links(page: str, base: str) -> list[tuple[str, str]]:
    out = []
    for href, text in ANCHOR.findall(page):
        href = html.unescape(href.strip())
        if SKIP.search(href):
            continue
        title = re.search(r"title\s*=\s*[\"']([^\"']+)", text)
        label = html.unescape(TAG.sub("", text)).strip() or (title.group(1) if title else "")
        u = urljoin(base, href)
        if u.startswith(("http://", "https://")):
            out.append((u.split("#")[0], re.sub(r"\s+", " ", label)[:60]))
    return out


def score(url: str, label: str) -> int:
    """How surely the link leads to campus postings: 0 not at all."""
    s = 0
    if system_of(url):
        s += 4
    if CAREERS.search(label):
        s += 3
    elif CAREER_URL.search(url):
        s += 2
    if s and (CAMPUS.search(label) or CAMPUS.search(url)):
        s += 2
    return s


TRACKING = re.compile(r"^(utm_\w+|timestamp__\d+|alichlgref|spm|from|session\w*)$", re.I)
POSTING_51JOB = re.compile(r"^/[a-z]+/\d+\.html$")   # jobs.51job.com/maoming/152174177.html: one posting
NOT_CAREERS = re.compile(r"/passport/|/security\.html$|/article_\d|botchallenge|/captcha", re.I)
LOGIN = re.compile(r"/Account/Login|/login(\.html?)?$", re.I)


def tidy(url: str) -> str | None:
    """The address as a careers site is kept: tracking and anti-bot parameters dropped (51job adds timestamp__1258
    and alichlgref, search pages s/t/req). None for an address that is one job posting rather than the employer's
    careers site."""
    u = urlsplit(url)
    host = (u.hostname or "").lower()
    if host == "jobs.51job.com" and POSTING_51JOB.match(u.path) and not u.path.startswith("/all/co"):
        return None
    if NOT_CAREERS.search(u.path):          # an anti-bot check or a news article
        return None
    back = dict(parse_qsl(u.query)).get("returnUrl", "")
    if LOGIN.search(u.path) and back.startswith(("http://", "https://")):
        return tidy(back)                    # a sign-in page in front of the careers page: the page itself
    # a sign-in page with nowhere to return to is the recruiting system's own entrance (zhaopin.tisco.com.cn): kept
    pairs = parse_qsl(u.query, keep_blank_values=True)
    keep = [(k, v) for k, v in pairs
            if not TRACKING.match(k) and not (host.endswith("51job.com") and k in ("s", "t", "req"))]
    if len(keep) == len(pairs):
        return url                           # nothing to drop: the address stays as it was, '#/route' and all
    return urlunsplit((u.scheme, u.netloc, u.path, urlencode(keep, safe="/:,[]{}\""), u.fragment))


def bot_check(page: str) -> bool:
    """A page that is only an anti-bot script (EdgeOne, 阿里云 WAF, 加速乐): its links appear in a browser alone."""
    return len(page) < 6000 and bool(BOT.search(page))


def homepage(url: str) -> tuple[int, str, str]:
    """The homepage as a visitor in mainland China would see it. Opened from abroad, many send the visitor to
    their foreign site (byd.com -> /au, midea.com -> /au, iflytek.com -> /en), whose links lead to no 校招, so the
    Chinese variants of the address are tried then."""
    status, final, page = fetch(url)
    if status and status < 400 and not ABROAD.search(urlsplit(final).path) and not urlsplit(final).hostname.startswith(("en.", "global.")):
        return status, final, page
    u = urlsplit(url)
    host = u.hostname or ""
    tries = [f"{u.scheme}://{host}/{p}" for p in ("cn", "zh", "zh-cn", "cn/zh", "zh_cn")]
    if host.endswith(".com"):
        tries.insert(0, f"{u.scheme}://{host}.cn")
    for t in tries:
        st, fin, pg = fetch(t, timeout=12)
        if st and st < 400 and pg and not ABROAD.search(urlsplit(fin).path):
            return st, fin, pg
    return status, final, page


def crawl(rec: dict) -> tuple[list[str], str]:
    """(candidate addresses best first, a note on what happened)."""
    home = rec.get("website") or ""
    status, final, page = homepage(home)
    if not status or status >= 400 or not page:
        return [], f"homepage: {'no answer' if not status else 'HTTP %d' % status}"
    if bot_check(page):
        return [], "homepage: anti-bot check (needs a browser)"
    found: dict[str, int] = {}
    for u, label in links(page, final):
        s = score(u, label)
        if s:
            found[u] = max(found.get(u, 0), s)
    for u in RAW.findall(page):   # a system's address in a script or a data attribute, not a link
        u = html.unescape(u).rstrip("\\/'\".,);")
        if system_of(u):
            found[u] = max(found.get(u, 0), 4)
    named = any(n.casefold() in page.casefold() for n in names(rec))
    # one step further from the best few that are not a system's address already (a 人才招聘 page linking out)
    for u in sorted((u for u in found if not system_of(u)), key=lambda u: -found[u])[:3]:
        st, fin, p = fetch(u)
        if not st or st >= 400 or not p:   # unreachable from here (often only from abroad): still a candidate
            continue
        if fin != u and score(fin, "") >= 2:
            found[fin] = max(found.get(fin, 0), found[u])
        for v, label in links(p, fin):
            s = score(v, label)
            if s >= 3:
                found[v] = max(found.get(v, 0), s + (1 if s >= 4 else 0))
    tidied: dict[str, int] = {}
    for u, s in found.items():
        t = tidy(u)
        if t:
            tidied[t] = max(tidied.get(t, 0), s)
    found = tidied
    ranked = sorted(found, key=lambda u: (-found[u], len(u)))
    note = f"homepage read{'' if named else ' (names no one: is the website right?)'}, {len(found)} recruiting links"
    return ranked[:5], note


def studio_detectors(path: Path | None):
    """Resume Studio's detectors (each url -> True / False / None), or [] when it isn't there."""
    if not path or not (path / "jobhunt" / "beisen.py").is_file():
        return []
    sys.path.insert(0, str(path))
    try:
        from jobhunt import alitalent, beisen, feishu, hotjob, iguopin  # noqa: PLC0415
    except Exception as e:   # an older checkout, say: the address-only rules still work
        print(f"Resume Studio's detectors couldn't be loaded ({e}); systems are told by address only")
        return []
    return [("国聘", iguopin.detect), ("HotJob", hotjob.detect), ("北森", beisen.detect), ("飞书", feishu.detect),
            ("阿里系", alitalent.detect)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sector", help="only data/cn/<sector>-*.jsonl")
    ap.add_argument("--limit", type=int, default=0, help="at most this many employers (a trial run)")
    ap.add_argument("--dry", action="store_true", help="report only, rewrite nothing")
    ap.add_argument("--file", help="one .jsonl file instead (a trial)")
    ap.add_argument("--new-only", action="store_true",
                    help="skip employers an earlier run already looked at with the same homepage")
    ap.add_argument("--studio", help="Resume Studio's folder (default: ../resume-studio beside this one)")
    args = ap.parse_args()
    studio = Path(args.studio) if args.studio else ROOT.parent / "resume-studio"
    detectors = studio_detectors(studio)
    files = [Path(args.file)] if args.file else sorted(
        (ROOT / "data" / "cn").glob(f"{args.sector}-*.jsonl" if args.sector else "*.jsonl"))
    content = {f: [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()] for f in files}
    work = [(f, r) for f, recs in content.items() for r in recs if r.get("website") and not r.get("campus_site")]
    if args.new_only:   # only employers no earlier run of this sector looked at (dist/find-report-<sector>.tsv)
        seen = set()
        for rep in (ROOT / "dist").glob("find-report-*.tsv"):
            for line in rep.read_text(encoding="utf-8").splitlines()[1:]:
                cols = line.split("\t")
                if len(cols) > 2:
                    seen.add((cols[0], cols[1], cols[2]))
        work = [(f, r) for f, r in work if (f.stem, r["name"], r["website"]) not in seen]
    if args.limit:
        work = work[:args.limit]
    print(f"{len(work)} employers to look for, {'with' if detectors else 'without'} Resume Studio's detectors")

    def one(item):
        f, r = item
        cands, note = crawl(r)
        cands = list(dict.fromkeys([*cands, *(r.get("site_candidates") or [])]))
        tried = []
        for u in cands[:4]:
            sys_name = system_of(u)
            if not sys_name:
                for name, det in detectors:
                    try:
                        if det(u):
                            sys_name = name
                            break
                    except Exception:   # a site that turns the request away, or any reader's error: not this one
                        continue
            if sys_name:
                tried.append((u, f"read by {sys_name}"))
                return item, u, sys_name, cands, note, tried
            ok, final, why = verdict(r, u)
            if ok and not (CAREER_URL.search(final) or CAREERS.search(final)):
                ok, why = False, why + ", but not a careers address"
            tried.append((u, why))
            if ok:
                return item, final, "", cands, note, tried
        return item, None, "", cands, note, tried

    month = time.strftime("%Y-%m")
    report, found = [], 0
    with cf.ThreadPoolExecutor(16) as pool:
        for n, (item, good, sys_name, cands, note, tried) in enumerate(pool.map(one, work), 1):
            f, r = item
            if good:
                found += 1
                r["campus_site"], r["checked"] = good, month
                r["system"] = sys_name or r.get("system") or ""
                r["sources"] = list(dict.fromkeys([*(r.get("sources") or []), good]))
                r["site_candidates"] = []
            elif cands:
                r["site_candidates"] = cands
            report.append(f"{f.stem}\t{r['name']}\t{r['website']}\t{note}\t{good or ''}\t{sys_name}\t"
                          + " | ".join(f"{u} ({why})" for u, why in tried))
            if n % 50 == 0:
                print(f"  {n}/{len(work)} looked at, {found} found", flush=True)
    print(f"{found} of {len(work)} careers sites found")
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    name = f"find-report{'-' + args.sector if args.sector else ''}{time.strftime('-new-%m%d%H%M') if args.new_only else ''}"
    (out / f"{name}.tsv").write_text("sector\temployer\twebsite\thomepage\tcareers site\tsystem\ttried\n"
                                          + "\n".join(report) + "\n", encoding="utf-8")
    if not args.dry:
        for f, recs in content.items():
            f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
