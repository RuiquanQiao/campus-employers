"""Split the employers with no homepage into batches for a search pass, and gather what the searches found.

    python scripts/search_batches.py split [--size 150]   # writes dist/search/todo-NN.tsv
    python scripts/search_batches.py gather               # dist/search/done-NN.tsv -> data/cn/<sector>.search.tsv

A todo line is `sector<TAB>name<TAB>full name<TAB>hq`; a done line is `sector<TAB>name<TAB>homepage<TAB>careers page`
(either may be empty). Gathered homepages are then checked like guesses:
`python scripts/check_websites.py --suffix search`.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "search"


def split(size: int) -> None:
    rows = []
    for f in sorted((ROOT / "data" / "cn").glob("*.jsonl")):
        sector = f.stem.rsplit("-", 1)[0]
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                r = json.loads(line)
                if not r.get("website"):
                    rows.append("\t".join([sector, r["name"], r.get("full_name") or "", r.get("hq") or ""]))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("todo-*.tsv"):
        old.unlink()
    n = 0
    for i in range(0, len(rows), size):
        n += 1
        (OUT / f"todo-{n:02d}.tsv").write_text("\n".join(rows[i:i + size]) + "\n", encoding="utf-8")
    print(f"{len(rows)} employers with no homepage, in {n} batches of {size}")


def gather() -> None:
    by_sector = collections.defaultdict(list)
    jobs_of = collections.defaultdict(list)
    careers = 0
    for f in sorted(OUT.glob("done-*.tsv")):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            parts = [p.strip() for p in line.split("\t")] + ["", "", "", ""]
            sector, name, home, jobs = parts[:4]
            if not (sector and name):
                continue
            if home.startswith(("http://", "https://")):
                by_sector[sector].append(f"{name}\t{home}")
            if jobs.startswith(("http://", "https://")):
                jobs_of[sector].append(f"{name}\t{jobs}")
                careers += 1
    for sector, lines in sorted(by_sector.items()):
        (ROOT / "data" / "cn" / f"{sector}.search.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{sector}: {len(lines)} found")
    for sector, lines in sorted(jobs_of.items()):   # careers pages: candidates for find_sites.py to confirm
        (ROOT / "data" / "cn" / f"{sector}.careers.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{sum(map(len, by_sector.values()))} homepages found by search, {careers} with a careers page beside")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["split", "gather"])
    ap.add_argument("--size", type=int, default=150)
    args = ap.parse_args()
    split(args.size) if args.step == "split" else gather()
    return 0


if __name__ == "__main__":
    sys.exit(main())
