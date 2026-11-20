"""Check every data/<country>/*.jsonl file; with --merge, write dist/<country>.json with duplicates merged.

    python scripts/validate.py [--merge]

Standard library only. Prints one line per file and the problems found; exits 1 when there are any.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
NATURES = {"cn.central_soe", "cn.local_soe", "cn.state_finance", "cn.private", "cn.foreign", "cn.public",
           "cn.university", "cn.civil"}
# outside mainland China: <country code>.<kind>, e.g. au.company, sg.government
KINDS = {"company", "state", "government", "research", "nonprofit"}
FIELDS = ["name", "full_name", "aliases", "nature", "industry", "sub", "parent", "hq", "cities", "listed", "scale",
          "funding", "campus_site", "system", "hires", "roles", "notes", "sources", "checked"]
LISTS = {"aliases", "cities", "hires", "roles", "sources", "site_candidates"}
OPTIONAL = {"site_candidates", "website"}   # unconfirmed careers addresses, and the homepage scripts/find_sites.py crawls
HIRES = {"校招", "实习", "社招", "graduate", "internship", "experienced"}


def key(name: str) -> str:
    s = re.sub(r"[\s\W_]+", "", str(name or "")).casefold()
    return re.sub(r"(股份)?有限(责任)?公司$|集团$|(pty)?(ltd|limited|inc|plc|llc|gmbh|ag|kk)$", "", s)


def nature_ok(nature: str, country: str) -> bool:
    if country == "cn":
        return nature in NATURES
    cc, _, kind = str(nature or "").partition(".")
    return cc == country and kind in KINDS


def check(rec: dict, country: str = "cn") -> list[str]:
    out = []
    missing = [f for f in FIELDS if f not in rec]
    extra = [f for f in rec if f not in FIELDS and f not in OPTIONAL]
    if missing:
        out.append("missing " + ",".join(missing))
    if extra:
        out.append("unknown " + ",".join(extra))
    if not str(rec.get("name") or "").strip():
        out.append("no name")
    if not nature_ok(rec.get("nature"), country):
        out.append(f"nature {rec.get('nature')!r}")
    for f in LISTS:
        if f in rec and not isinstance(rec[f], list):
            out.append(f"{f} is not a list")
    for f in rec.get("site_candidates") or []:
        if not (isinstance(f, str) and f.startswith(("http://", "https://"))):
            out.append(f"site_candidates {f!r}")
    web = rec.get("website")
    if web is not None and not (isinstance(web, str) and (web == "" or web.startswith(("http://", "https://")))):
        out.append(f"website {web!r}")
    for f in set(FIELDS) - LISTS:
        if f in rec and not isinstance(rec[f], str):
            out.append(f"{f} is not text")
    url = rec.get("campus_site") or ""
    if url and not (url.startswith(("http://", "https://")) and urlsplit(url).hostname):
        out.append(f"campus_site {url!r}")
    if url and not rec.get("sources"):
        out.append("a careers site with no source")
    bad = [h for h in rec.get("hires") or [] if h not in HIRES]
    if bad:
        out.append(f"hires {bad}")
    if rec.get("checked") and not re.fullmatch(r"20\d\d-\d\d", rec["checked"]):
        out.append(f"checked {rec['checked']!r}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()
    problems = 0
    for country in sorted(p for p in (ROOT / "data").iterdir() if p.is_dir()):
        seen: dict[str, tuple[str, dict]] = {}
        merged: list[dict] = []
        total = sites = 0
        for f in sorted(country.glob("*.jsonl")):   # <sector>-NN.jsonl: one file per batch
            n = 0
            for i, line in enumerate(f.read_text(encoding="utf-8-sig").splitlines(), 1):   # a BOM (PowerShell's) is fine
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except ValueError as e:
                    print(f"  {f.name}:{i}: not JSON ({e})")
                    problems += 1
                    continue
                n += 1
                for p in check(rec, country.name):
                    print(f"  {f.name}:{i} {rec.get('name')}: {p}")
                    problems += 1
                k = key(rec.get("name"))
                if k in seen:
                    other_file, other = seen[k]
                    # the same employer in two sectors: keep the fuller record, its sectors noted
                    if sum(bool(rec.get(x)) for x in FIELDS) > sum(bool(other.get(x)) for x in FIELDS):
                        merged[merged.index(other)] = rec
                        seen[k] = (f.name, rec)
                    continue
                seen[k] = (f.name, rec)
                merged.append(rec)
            total += n
            print(f"{country.name}/{f.name}: {n}")
        sites = sum(bool(r.get("campus_site")) for r in merged)
        print(f"{country.name}: {total} lines, {len(merged)} employers, {sites} with a careers site")
        if args.merge:
            out = ROOT / "dist" / f"{country.name}.json"
            out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps(merged, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
