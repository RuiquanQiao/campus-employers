"""Per sector: employers, with a homepage (`website`), with a careers site, and how many of those a system reads.

    python scripts/coverage.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    rows = collections.defaultdict(lambda: [0, 0, 0, 0])
    for f in sorted((ROOT / "data" / "cn").glob("*.jsonl")):
        sector = f.stem.rsplit("-", 1)[0]
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                r = json.loads(line)
                row = rows[sector]
                row[0] += 1
                row[1] += bool(r.get("website"))
                row[2] += bool(r.get("campus_site"))
                row[3] += bool(r.get("campus_site") and r.get("system"))
    print(f"{'sector':20}{'employers':>10}{'homepage':>10}{'careers':>9}{'system':>8}")
    for s, (n, w, c, y) in sorted(rows.items()):
        print(f"{s:20}{n:>10}{w:>10}{c:>9}{y:>8}")
    tot = [sum(r[i] for r in rows.values()) for i in range(4)]
    print(f"{'all':20}{tot[0]:>10}{tot[1]:>10}{tot[2]:>9}{tot[3]:>8}")


if __name__ == "__main__":
    main()
