"""The graduate-page check (CHECK_BRIEF.md): split a country into batches, then apply what the agents read.

    python scripts/checks.py split <cc> [--size 60]    writes dist/checks/<cc>-NN.in.jsonl from dist/<cc>.json
    python scripts/checks.py apply <cc> [--dry]        reads dist/checks/<cc>-NN.out.jsonl into data/<cc>/*.jsonl

apply, for each `confirmed` line: sets `notes` when the page stated who may apply, `hires` from the page, the
careers site when the record has none, adds the page to `sources` and stamps `checked`. `no_intake` lines are
listed in dist/checks/<cc>-no-intake.tsv to be looked at; nothing is removed here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "checks"
HIRES = {"graduate", "internship", "experienced"}
JOB_BOARDS = __import__("re").compile(r"gradconnection|prosple|seek\.com|indeed\.|linkedin\.com|glassdoor|"
                                      r"gradaustralia|careerone|jora\.|handshake|joinhandshake|ziprecruiter|"
                                      r"hatch\.team|graduateopportunities|studentjob|wayup|vault\.com", 2)


def split(cc: str, size: int) -> int:
    recs = json.loads((ROOT / "dist" / f"{cc}.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    # a later split adds batches after the ones already handed out, for employers in none of them
    given, last = set(), 0
    for f in OUT.glob(f"{cc}-*.in.jsonl"):
        last = max(last, int(f.name.split("-")[-1].split(".")[0]))
        given |= {json.loads(x)["name"] for x in f.read_text(encoding="utf-8").splitlines() if x.strip()}
    recs = [r for r in recs if r["name"] not in given]
    for i in range(0, len(recs), size):
        lines = [json.dumps({k: r.get(k) or ("" if k != "site_candidates" else [])
                             for k in ("name", "website", "campus_site", "site_candidates")}, ensure_ascii=False)
                 for r in recs[i:i + size]]
        (OUT / f"{cc}-{last + i // size + 1:02d}.in.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{cc}: {len(recs)} employers in {(len(recs) + size - 1) // size} new batches of {size} after {last}")
    return 0


def apply(cc: str, dry: bool) -> int:
    results: dict[str, dict] = {}
    bad = 0
    for f in sorted(OUT.glob(f"{cc}-*.out.jsonl")):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            results[r.get("name", "")] = r
    month = time.strftime("%Y-%m")
    stats = {"confirmed": 0, "notes": 0, "site": 0, "no_intake": 0, "unreachable": 0, "unmatched": 0}
    seen = set()
    no_intake = []
    for f in sorted((ROOT / "data" / cc).glob("*.jsonl")):
        recs = [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
        changed = False
        for rec in recs:
            r = results.get(rec["name"])
            if not r or rec["name"] in seen:
                continue
            seen.add(rec["name"])
            status = r.get("status")
            if status in ("no_intake", "careers_only"):
                stats["no_intake"] += 1
                no_intake.append(f"{rec['name']}\t{r.get('programme', '')}\t{f.name}")
                continue
            if status != "confirmed":
                stats["unreachable"] += 1
                continue
            page = (r.get("programme") or "").strip()
            # a job board's listing is not the employer's own word: the line is left for the second pass
            if JOB_BOARDS.search(page):
                stats["job_board"] = stats.get("job_board", 0) + 1
                continue
            stats["confirmed"] += 1
            if (r.get("notes") or "").strip():
                rec["notes"] = r["notes"].strip()
                stats["notes"] += 1
            hires = [h for h in (r.get("hires") or []) if h in HIRES]
            if hires:
                rec["hires"] = hires
            if page.startswith("http"):
                if not rec.get("campus_site"):
                    rec["campus_site"] = page
                    stats["site"] += 1
                rec["sources"] = list(dict.fromkeys([*(rec.get("sources") or []), page]))
            rec["checked"] = month
            changed = True
        if changed and not dry:
            f.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs), encoding="utf-8")
    stats["unmatched"] = len(set(results) - seen)
    if not dry:
        (OUT / f"{cc}-no-intake.tsv").write_text("employer\tpage\tfile\n" + "\n".join(no_intake) + "\n",
                                                 encoding="utf-8")
    print(f"{cc}: {stats} ({bad} unreadable lines)" + (" [dry run]" if dry else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "apply"])
    ap.add_argument("cc")
    ap.add_argument("--size", type=int, default=60)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    return split(a.cc, a.size) if a.cmd == "split" else apply(a.cc, a.dry)


if __name__ == "__main__":
    sys.exit(main())
