"""Check the guessed homepages in data/cn/<sector>.guesses.tsv and keep the ones that are right. No AI, no search.

    python scripts/check_websites.py [--country jp] [--sector banks] [--dry]

Each line of a guesses file is `name<TAB>address<TAB>address…`, best guess first, for employers with no `website`.
Each address is opened (redirects followed); the first that answers and whose page names the employer (its name, full
name, an alias, or the full name without 有限公司/集团) becomes its `website`. What was tried goes to
dist/website-report.tsv; employers none of whose guesses held keep `website` "".
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_sites import GONE, fetch, names  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def holds(rec: dict, url: str) -> tuple[str | None, str]:
    """(the homepage to keep, or None; why)."""
    status, final, text = fetch(url, timeout=15)
    if not status:
        return None, "no answer"
    if status >= 400:
        return None, f"HTTP {status}"
    if GONE.search(text[:5000]):
        return None, "page says it doesn't exist"
    low = html.unescape(text[:300_000]).casefold()   # a page may spell its name as &#x677E;&#x5C71;… (sslab.org.cn)
    hit = next((n for n in names(rec) if n.casefold() in low), "")
    if not hit:
        return None, "answers but names no one"
    # the address as given, unless it redirected to another site (an old domain moved to a new one)
    keep = url if (final.split("/")[2] if "//" in final else final) == url.split("/")[2] else final
    return keep, f"names {hit}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="cn", help="data/<country>/ (cn, gb, jp, de…)")
    ap.add_argument("--sector")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--suffix", default="guesses", help="guesses (agents' guesses) or search (found by search)")
    args = ap.parse_args()
    report = []
    for tsv in sorted((ROOT / "data" / args.country).glob(f"{args.sector or '*'}.{args.suffix}.tsv")):
        sector = tsv.name[: -len(f".{args.suffix}.tsv")]
        guesses = {}
        for line in tsv.read_text(encoding="utf-8-sig").splitlines():
            name, *urls = [x.strip() for x in line.split("\t")]
            urls = [u for u in urls if u.startswith(("http://", "https://"))]
            if name and urls:
                guesses[name] = urls
        files = [f for f in sorted((ROOT / "data" / args.country).glob(f"{sector}-*.jsonl"))
                 if f.stem.removeprefix(sector + "-").isdigit()]
        content = {f: [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()] for f in files}
        work = [r for recs in content.values() for r in recs if not r.get("website") and r.get("name") in guesses]

        def one(r):
            tried = []
            for u in guesses[r["name"]][:3]:
                keep, why = holds(r, u)
                tried.append((u, why))
                if keep:
                    return r, keep, tried
            # a search result is evidence a guess is not: one that only can't be reached from here (many state-owned
            # sites answer nobody outside mainland China, or turn foreign visitors away) is kept; one that answers and
            # names someone else, or says it doesn't exist, is not
            if args.suffix == "search" and all(w == "no answer" or w in ("HTTP 403", "HTTP 412") or w.startswith("HTTP 5")
                                               for _, w in tried):
                return r, guesses[r["name"]][0], tried + [("", "kept: found by search, unreachable from here")]
            return r, None, tried

        found = 0
        with cf.ThreadPoolExecutor(24) as pool:
            for r, keep, tried in pool.map(one, work):
                if keep:
                    found += 1
                    r["website"] = keep
                report.append(f"{sector}\t{r['name']}\t{keep or ''}\t" + " | ".join(f"{u} ({w})" for u, w in tried))
        print(f"{sector}: {found} of {len(work)} guessed homepages hold ({len(guesses) - len(work)} guesses for names "
              "not found or already with a homepage)", flush=True)
        if not args.dry:
            for f, recs in content.items():
                f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    cc = "" if args.country == "cn" else args.country + "-"
    (out / f"website-report-{cc}{args.suffix}{'-' + args.sector if args.sector else ''}.tsv").write_text("sector\temployer\thomepage\ttried\n" + "\n".join(report) + "\n",
                                             encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
