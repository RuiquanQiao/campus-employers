"""Lists for the knowledge pass (FLAG_BRIEF.md): the employers whose latest check line is not `confirmed`.

    python scripts/flag_lists.py <cc> [--size 500]        writes dist/checks/<cc>-flag-NN.in.tsv
    python scripts/flag_lists.py <cc> --batches [--size 40]   reads dist/checks/<cc>-flag-NN.out.tsv and writes the
                                                            flagged employers as recheck batches (<cc>-rNN.in.jsonl)

An agent marks, from what it knows and with no web search, the employers known to run a graduate, intern, vacation
or cadet programme in the country; only those go to the second look (RECHECK_BRIEF.md), which needs searches.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "checks"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import latest  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cc")
    ap.add_argument("--size", type=int, default=0)
    ap.add_argument("--batches", action="store_true")
    a = ap.parse_args()
    results = latest(a.cc)
    recs = json.loads((ROOT / "dist" / f"{a.cc}.json").read_text(encoding="utf-8"))
    todo = [r for r in recs if results.get(r["name"], {}).get("status") != "confirmed"]
    if not a.batches:
        size = a.size or 500
        for i in range(0, len(todo), size):
            rows = [f"{r['name']}\t{r.get('industry', '')} / {r.get('sub', '')}\t{r.get('website', '')}"
                    for r in todo[i:i + size]]
            (OUT / f"{a.cc}-flag-{i // size + 1:02d}.in.tsv").write_text("name\tline of business\twebsite\n"
                                                                     + "\n".join(rows) + "\n", encoding="utf-8")
        print(f"{a.cc}: {len(todo)} employers not confirmed, in {(len(todo) + size - 1) // size} lists")
        return 0
    flagged = set()
    for f in sorted(OUT.glob(f"{a.cc}-flag-*.out.tsv")):
        for line in f.read_text(encoding="utf-8").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1].strip() == "yes":
                flagged.add(parts[0].strip())
    # those already given a second look are not given another
    given = set()
    for f in OUT.glob(f"{a.cc}-r*.out.jsonl"):
        given |= {json.loads(x)["name"] for x in f.read_text(encoding="utf-8").splitlines() if x.strip()}
    pick = [r for r in todo if r["name"] in flagged and r["name"] not in given]
    size = a.size or 40
    last = max([int(f.name.split("-r")[-1].split(".")[0]) for f in OUT.glob(f"{a.cc}-r*.in.jsonl")] or [0])
    for i in range(0, len(pick), size):
        lines = [json.dumps({"name": r["name"], "website": r.get("website") or "", "campus_site": r.get("campus_site") or "",
                             "site_candidates": r.get("site_candidates") or [],
                             "first_pass": results.get(r["name"], {}).get("status", ""),
                             "first_page": results.get(r["name"], {}).get("programme") or ""}, ensure_ascii=False)
                 for r in pick[i:i + size]]
        (OUT / f"{a.cc}-r{last + i // size + 1:02d}.in.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{a.cc}: {len(flagged)} flagged, {len(pick)} not yet given a second look, in "
          f"{(len(pick) + size - 1) // size} batches after r{last:02d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
