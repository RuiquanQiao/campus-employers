"""Open every candidate careers page and keep the one that works and names the employer. No AI, no search.

    python scripts/verify_sites.py [--sector banks] [--recheck] [--dry]

For each line with `site_candidates` (and, with --recheck, its `campus_site` too), each address is opened (redirects
followed, 20 s at most, 16 at a time). An address counts when it answers 2xx and its page names the employer: its
name, full name or an alias in the page's text or title, or the employer's own domain in the final address. The first
one that counts becomes `campus_site` (`checked` set to this month, the address added to `sources`, the candidates
cleared). One that answers but names no one is kept as a candidate and listed in dist/verify-report.tsv, with why,
for a person or a later search to settle. Standard library only; files are rewritten in place, one line per employer.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import html
import http.client
import urllib.parse
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
CTX = ssl.create_default_context()
LOOSE = ssl._create_unverified_context()   # many 国企 sites serve an incomplete chain; the page itself is still read
GONE = re.compile(r"租户不存在|页面不存在|404 not found|page not found|找不到页面|站点不存在|域名.*未备案|该域名|网站已关停|网站已关闭", re.I)


def decode(raw: bytes, declared: str = "") -> str:
    """UTF-8 when the bytes are valid UTF-8 (many sites declare gb2312 and serve UTF-8), else the declared charset,
    else GB18030 (which covers GBK and GB2312)."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:3000])
    for cs in (declared, m.group(1).decode("ascii", "replace") if m else ""):
        cs = "gb18030" if cs.lower() in ("gb2312", "gbk") else cs
        if cs and cs.lower().replace("-", "") != "utf8":
            try:
                return raw.decode(cs)
            except (LookupError, UnicodeDecodeError):
                pass
    return raw.decode("gb18030", errors="replace")


def fetch(url: str, timeout: float = 20.0) -> tuple[int, str, str]:
    """(status, final address, decoded text up to 400 KB); status 0 when it couldn't be reached."""
    # an address as a page writes it may hold spaces or Chinese (/about us/joinus/): sent percent-encoded
    url = urllib.parse.quote(url.strip(), safe=":/?#[]@!$&'()*+,;=%~")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
                                              "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Encoding": "gzip, deflate"})
    for ctx in (CTX, LOOSE):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read(400_000)
                enc = (r.headers.get("Content-Encoding") or "").lower()
                if enc == "gzip":
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    raw = zlib.decompress(raw)
                return r.status, r.geturl(), decode(raw, r.headers.get_content_charset() or "")
        except ssl.SSLError:
            continue
        except urllib.error.HTTPError as e:
            return e.code, url, ""
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError, EOFError, zlib.error):
            if ctx is CTX:
                continue
            return 0, url, ""
    return 0, url, ""


def names(rec: dict) -> list[str]:
    out = [rec.get("name") or "", rec.get("full_name") or "", *(rec.get("aliases") or [])]
    short = re.sub(r"(股份)?有限(责任)?公司$|集团$|（.*?）|\(.*?\)", "", rec.get("full_name") or "")
    more = []
    for n in [rec.get("name") or "", rec.get("full_name") or ""]:
        # an institute named with a note and its parent, 上海航天技术研究院（航天八院） or 中国船舶集团第七二六研究所: its own
        # site says 上海航天技术研究院 / 航天八院 / 第七二六研究所, without the parent
        bare = re.sub(r"（.*?）|\(.*?\)", "", n).strip()
        more += [bare, *re.findall(r"[（(]([^）)]{3,})[）)]", n)]
        m = re.match(r"(中国[^第]{0,12}?集团(?:有限公司|公司)?|航空工业|中国航发|航天科技|航天科工|中国电科|中国农业科学院|中国医学科学院|"
                     r"中国科学院|中国工程物理研究院|中国商飞)(.{4,})$", bare)
        if m:
            more.append(m.group(m.lastindex))
    return [n for n in dict.fromkeys([*out, short, *more]) if len(n.strip()) >= 2 and not re.fullmatch(r"\d+所", n.strip())]


def verdict(rec: dict, url: str) -> tuple[bool, str, str]:
    """(it counts, the address to keep, why)."""
    status, final, text = fetch(url)
    if not status:
        return False, url, "no answer"
    if status >= 400:
        return False, url, f"HTTP {status}"
    head = html.unescape(text[:200_000])   # a page may spell its name as &#x677E;&#x5C71;… (sslab.org.cn)
    if GONE.search(head[:5000]):
        return False, final, "page says it doesn't exist"
    low = head.casefold()
    hit = next((n for n in names(rec) if n.casefold() in low), "")
    if hit:
        return True, final, f"names {hit}"
    # a single-page app's shell names nobody; its address on the company's own domain is enough
    host = (urlsplit(final).hostname or "").lower()
    own = [s for s in rec.get("sources") or [] if s] + [rec.get("campus_site") or ""]
    domains = {".".join((urlsplit(u).hostname or "").lower().split(".")[-2:]) for u in own if u}
    if host and ".".join(host.split(".")[-2:]) in domains - {"", "zhiye.com", "mokahr.com", "hotjob.cn", "feishu.cn", "iguopin.com"}:
        return True, final, "its own domain"
    return False, final, "answers but names no one"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sector", help="only data/cn/<sector>-*.jsonl")
    ap.add_argument("--recheck", action="store_true", help="also open each confirmed campus_site")
    ap.add_argument("--dry", action="store_true", help="report only, rewrite nothing")
    args = ap.parse_args()
    files = sorted((ROOT / "data" / "cn").glob(f"{args.sector}-*.jsonl" if args.sector else "*.jsonl"))
    work = []   # (file, line index, record, [addresses])
    content = {}
    for f in files:
        recs = [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
        content[f] = recs
        for i, r in enumerate(recs):
            urls = list(r.get("site_candidates") or [])
            if args.recheck and r.get("campus_site"):
                urls.insert(0, r["campus_site"])
            if urls:
                work.append((f, i, r, urls))
    print(f"{len(work)} employers to check in {len(files)} files")
    month = time.strftime("%Y-%m")
    report = []
    confirmed = 0

    def one(item):
        f, i, r, urls = item
        tried = []
        for u in urls:
            ok, final, why = verdict(r, u)
            tried.append((u, why))
            if ok:
                return item, final, tried
        return item, None, tried

    with cf.ThreadPoolExecutor(16) as pool:
        for n, (item, good, tried) in enumerate(pool.map(one, work), 1):
            f, i, r, urls = item
            if good:
                confirmed += 1
                r["campus_site"], r["checked"] = good, month
                r["sources"] = list(dict.fromkeys([*(r.get("sources") or []), good]))
                r["site_candidates"] = []
            for u, why in tried:
                report.append(f"{f.stem}\t{r['name']}\t{u}\t{why}\t{'kept' if good == u or (good and u == tried[-1][0]) else ''}")
            if n % 50 == 0:
                print(f"  {n}/{len(work)} checked, {confirmed} confirmed", flush=True)
    print(f"{confirmed} of {len(work)} confirmed")
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    (out / "verify-report.tsv").write_text("sector\temployer\taddress\tresult\t\n" + "\n".join(report) + "\n", encoding="utf-8")
    if not args.dry:
        for f, recs in content.items():
            f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
