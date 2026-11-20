"""Put the homepages listed in data/cn/<sector>.websites.tsv (name<TAB>address) into that sector's lines.

    python scripts/apply_websites.py [--sector new-energy]

A line already carrying a `website` keeps it. Names not found in the sector are printed. Standard library only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    only = sys.argv[sys.argv.index("--sector") + 1] if "--sector" in sys.argv else "*"
    for tsv in sorted((ROOT / "data" / "cn").glob(f"{only}.websites.tsv")):
        sector = tsv.name[: -len(".websites.tsv")]
        sites = {}
        for line in tsv.read_text(encoding="utf-8-sig").splitlines():
            name, _, url = line.partition("\t")
            url = url.strip()
            if name.strip() and url.startswith(("http://", "https://")):
                sites[name.strip()] = url
        used = set()
        set_ = 0
        for f in sorted((ROOT / "data" / "cn").glob(f"{sector}-*.jsonl")):
            if not f.stem.removeprefix(sector + "-").isdigit():
                continue   # another sector whose name starts the same (local-soe-east vs local-soe-east-x)
            recs = [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
            for r in recs:
                url = sites.get(r.get("name", ""))
                if url:
                    used.add(r["name"])
                    if not r.get("website"):
                        r["website"] = url
                        set_ += 1
                r.setdefault("website", "")
                r.setdefault("site_candidates", [])
            f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
        missing = [n for n in sites if n not in used]
        print(f"{sector}: {set_} homepages set, {len(missing)} names not found" + (f": {', '.join(missing[:10])}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
