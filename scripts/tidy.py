"""Clear `roles` lists that were copied across a sub-sector instead of known for each employer.

    python scripts/tidy.py [--dry] [--min 4]

A `roles` list held, word for word, by at least --min employers of one sector is a template, not a fact about any of
them: it is emptied on every one of them. Files are rewritten in place.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--min", type=int, default=4)
    args = ap.parse_args()
    by_sector = collections.defaultdict(list)
    content = {}
    for f in sorted((ROOT / "data" / "cn").glob("*.jsonl")):
        recs = [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
        content[f] = recs
        by_sector[f.stem.rsplit("-", 1)[0]].extend(recs)
    cleared = 0
    for sector, recs in sorted(by_sector.items()):
        counts = collections.Counter(tuple(r.get("roles") or []) for r in recs if r.get("roles"))
        templates = {k for k, n in counts.items() if n >= args.min}
        hit = [r for r in recs if tuple(r.get("roles") or []) in templates]
        for r in hit:
            r["roles"] = []
        cleared += len(hit)
        if hit:
            print(f"{sector}: {len(hit)} of {len(recs)} cleared ({len(templates)} lists used {args.min}+ times)")
    print(f"{cleared} roles lists cleared")
    if not args.dry:
        for f, recs in content.items():
            f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
