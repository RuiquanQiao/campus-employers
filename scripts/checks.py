"""The graduate-page check (CHECK_BRIEF.md): split a country into batches, then apply what the agents read.

    python scripts/checks.py split <cc> [--size 60]    writes dist/checks/<cc>-NN.in.jsonl from dist/<cc>.json
    python scripts/checks.py recheck <cc> [--listed]   second pass: dist/checks/<cc>-rNN.in.jsonl (RECHECK_BRIEF.md)
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


def recheck(cc: str, size: int, listed: bool) -> int:
    """Second pass (RECHECK_BRIEF.md): the employers whose latest line is careers_only or unreachable, in batches
    dist/checks/<cc>-rNN.in.jsonl, each with the page the first pass read. --listed keeps listed companies only."""
    results = latest(cc)
    recs = json.loads((ROOT / "dist" / f"{cc}.json").read_text(encoding="utf-8"))
    given = set()
    for f in OUT.glob(f"{cc}-r*.in.jsonl"):
        given |= {json.loads(x)["name"] for x in f.read_text(encoding="utf-8").splitlines() if x.strip()}
    todo = [r for r in recs if r["name"] in results and r["name"] not in given
            and results[r["name"]].get("status") in ("careers_only", "unreachable", "no_intake")
            and (not listed or r.get("listed"))]
    last = max([int(f.name.split("-r")[-1].split(".")[0]) for f in OUT.glob(f"{cc}-r*.in.jsonl")] or [0])
    for i in range(0, len(todo), size):
        lines = [json.dumps({"name": r["name"], "website": r.get("website") or "", "campus_site": r.get("campus_site") or "",
                             "site_candidates": r.get("site_candidates") or [],
                             "first_pass": results[r["name"]].get("status"),
                             "first_page": results[r["name"]].get("programme") or ""}, ensure_ascii=False)
                 for r in todo[i:i + size]]
        (OUT / f"{cc}-r{last + i // size + 1:02d}.in.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{cc}: {len(todo)} employers in {(len(todo) + size - 1) // size} recheck batches of {size} after r{last:02d}")
    return 0


def latest(cc: str, skip: str = "") -> dict[str, dict]:
    """Each employer's latest line: the first pass (<cc>-NN), then the second (<cc>-ats, <cc>-rNN) over it."""
    results: dict[str, dict] = {}
    for f in sorted(OUT.glob(f"{cc}-*.out.jsonl")):
        if f.name == skip:
            continue
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            try:
                r = json.loads(line) if line.strip() else None
            except json.JSONDecodeError:
                r = None
            if r and keep(results.get(r.get("name", "")), r):
                results[r.get("name", "")] = r
    return results


def keep(old: dict | None, new: dict) -> bool:
    """A later line replaces an earlier one, except that a confirmation stays until another confirmation."""
    return old is None or old.get("status") != "confirmed" or new.get("status") == "confirmed"


def apply(cc: str, dry: bool) -> int:
    results: dict[str, dict] = {}
    bad = 0
    # sorted: <cc>-NN (first pass) before <cc>-rNN (second pass), so a second-pass line replaces the first
    for f in sorted(OUT.glob(f"{cc}-*.out.jsonl")):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            if keep(results.get(r.get("name", "")), r):
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
            # a confirmation names the employer's own page; one without a page is only the agent's word
            if not page.startswith("http"):
                stats["no_page"] = stats.get("no_page", 0) + 1
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
    ap.add_argument("cmd", choices=["split", "recheck", "apply"])
    ap.add_argument("cc")
    ap.add_argument("--size", type=int, default=60)
    ap.add_argument("--listed", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.cmd == "recheck":
        return recheck(a.cc, a.size, a.listed)
    return split(a.cc, a.size) if a.cmd == "split" else apply(a.cc, a.dry)


if __name__ == "__main__":
    sys.exit(main())
