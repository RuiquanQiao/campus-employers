"""Write the showcase page's data: docs/data/<country>.json and docs/data/index.json, from dist/<country>.json.

    python scripts/validate.py --merge && python scripts/build_site.py

Each employer becomes a short list of the fields the page shows (the order is FIELDS below); working fields
(sources, checked, site_candidates) are left out. index.json lists the countries with their counts.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["name", "full_name", "aliases", "nature", "industry", "sub", "parent", "hq", "cities", "listed", "scale",
          "website", "campus_site", "system", "hires", "roles", "notes"]
ORDER = ["cn", "au", "sg", "hk", "gb", "us", "jp", "de"]


def main() -> int:
    out = ROOT / "docs" / "data"
    out.mkdir(parents=True, exist_ok=True)
    countries = []
    for f in sorted((ROOT / "dist").glob("*.json"), key=lambda p: (ORDER.index(p.stem) if p.stem in ORDER else 99, p.stem)):
        if len(f.stem) != 2:
            continue
        recs = json.loads(f.read_text(encoding="utf-8"))
        rows = [[r.get(k) or ("" if k not in ("aliases", "cities", "hires", "roles") else []) for k in FIELDS]
                for r in recs]
        body = json.dumps({"fields": FIELDS, "rows": rows}, ensure_ascii=False, separators=(",", ":"))
        (out / f"{f.stem}.json").write_text(body, encoding="utf-8")
        countries.append({"code": f.stem, "employers": len(recs),
                          "careers": sum(bool(r.get("campus_site")) for r in recs),
                          "system": sum(bool(r.get("system")) for r in recs),
                          "sha": hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]})
        print(f"{f.stem}: {len(recs)} employers")
    # "version" is the build time, so a copy built later the same day is still told apart; "sha" lets a reader
    # download only the countries whose file changed.
    index = {"updated": time.strftime("%Y-%m-%d"), "version": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "countries": countries}
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
