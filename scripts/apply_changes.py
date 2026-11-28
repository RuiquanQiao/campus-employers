"""Apply dist/search/actions.tsv (corrections found by search, one action per line) to data/cn/*.jsonl, and
dist/search/<cc>-actions.tsv to another country's data/<cc>/*.jsonl (removed lines listed in dist/removed-<cc>.tsv).

    python scripts/apply_changes.py [--cc us] [--dry]

Each line is `name<TAB>action<TAB>value<TAB>reason`. Actions:
  remove     the employer no longer recruits on its own; its line goes (listed in dist/removed.tsv with why)
  merge      the same employer as the record named in value: that record takes this one's names as aliases, its
             cities, and any homepage / careers site it lacks; this line goes
  rename     value is {"name": …, "full_name": …}; the old names become aliases
  full_name / parent / nature / hq / website / campus_site / alias   set (or, for alias, add) that field;
             "-" as the value empties it
  skip / missing   nothing
Renames run first, so a merge or remove may name a record by its new name.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER = {"rename": 0, "full_name": 1, "parent": 1, "nature": 1, "hq": 1, "alias": 1, "website": 1, "campus_site": 1, "merge": 2, "remove": 3}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cc", default="cn")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    cn = args.cc == "cn"
    files = [f for f in sorted((ROOT / "data" / args.cc).glob("*.jsonl"))]
    content = {f: [json.loads(x) for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()] for f in files}
    by_name: dict[str, dict] = {}
    for recs in content.values():
        for r in recs:
            by_name.setdefault(r["name"], r)
    actions = []
    for line in (ROOT / "dist" / "search" / ("actions.tsv" if cn else f"{args.cc}-actions.tsv")).read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 4 and parts[1] in ORDER:
            actions.append(parts)
    actions.sort(key=lambda a: ORDER[a[1]])
    gone: set[int] = set()
    removed, done, problems = [], 0, []
    renamed: dict[str, str] = {}

    def find(name: str) -> dict | None:
        return by_name.get(renamed.get(name, name))

    for name, act, value, why in actions:
        r = find(name)
        if r is None or id(r) in gone:
            problems.append(f"{name}: no record for {act}")
            continue
        if act == "rename":
            v = json.loads(value)
            old = [r["name"], r.get("full_name") or ""]
            if v.get("name"):
                r["name"] = v["name"]
            if v.get("full_name"):
                r["full_name"] = v["full_name"]
            r["aliases"] = [a for a in dict.fromkeys([*(r.get("aliases") or []), *old])
                            if a and a not in (r["name"], r["full_name"])]
            renamed[name] = r["name"]
            by_name[r["name"]] = r
        elif act == "alias":
            r["aliases"] = list(dict.fromkeys([*(r.get("aliases") or []), value]))
        elif act in ("full_name", "parent", "nature", "hq", "website", "campus_site"):
            r[act] = "" if value == "-" else value
            if act == "hq" and value not in (r.get("cities") or []):
                r["cities"] = [value, *(r.get("cities") or [])]
        elif act == "merge":
            t = find(value)
            if t is None or t is r:
                problems.append(f"{name}: merge target {value} not found")
                continue
            t["aliases"] = [a for a in dict.fromkeys([*(t.get("aliases") or []), r["name"], r.get("full_name") or "",
                                                      *(r.get("aliases") or [])]) if a and a not in (t["name"], t.get("full_name"))]
            t["cities"] = list(dict.fromkeys([*(t.get("cities") or []), *(r.get("cities") or [])]))
            for k in ("website", "campus_site", "system", "notes", "hires", "checked", "full_name"):
                if not t.get(k) and r.get(k):
                    t[k] = r[k]
            t["sources"] = list(dict.fromkeys([*(t.get("sources") or []), *(r.get("sources") or [])]))
            gone.add(id(r))
            removed.append(f"{r['name']}\tmerged into {t['name']}\t{why}")
        elif act == "remove":
            gone.add(id(r))
            removed.append(f"{r['name']}\tremoved{' (now ' + value + ')' if value and value != 'none' else ''}\t{why}")
        done += 1
    print(f"{done} actions applied, {len(gone)} lines removed or merged, {len(problems)} problems")
    for p in problems:
        print("  " + p)
    if not args.dry:
        for f, recs in content.items():
            f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs if id(r) not in gone),
                         encoding="utf-8")
        listing = ROOT / "dist" / ("removed.tsv" if cn else f"removed-{args.cc}.tsv")
        # an action file keeps every action ever applied; one applied before finds no record now, and its line
        # in the listing stays
        before = listing.read_text(encoding="utf-8").splitlines()[1:] if listing.is_file() else []
        kept = list(dict.fromkeys([*before, *removed]))
        listing.write_text("employer\tchange\twhy\n" + "\n".join(kept) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
