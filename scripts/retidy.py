"""Put every kept `campus_site` through find_sites.tidy: tracking parameters dropped, and an address that is one job
posting cleared (with its `system`), so the next crawl looks again.

    python scripts/retidy.py [--dry]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from find_sites import tidy  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    changed = cleared = 0
    for f in sorted((ROOT / "data" / "cn").glob("*.jsonl")):
        recs = [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
        touched = False
        for r in recs:
            old = r.get("campus_site") or ""
            if not old:
                continue
            new = tidy(old)
            if new is None:
                print(f"cleared  {r['name']}: {old[:90]}")
                r["campus_site"], r["system"] = "", ""
                cleared += 1
                touched = True
            elif new != old:
                print(f"tidied   {r['name']}: {new[:90]}")
                r["campus_site"] = new
                changed += 1
                touched = True
        if touched and not args.dry:
            f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    print(f"{changed} tidied, {cleared} cleared{' (dry run)' if args.dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
