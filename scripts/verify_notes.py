"""Check that each eligibility note from the graduate-page check rests on a sentence the employer's page really has.

    python scripts/verify_notes.py <cc>

For every confirmed line in dist/checks/<cc>-*.out.jsonl with `notes` and `evidence`, the `programme` page is opened
and the evidence sentence looked for in its text (spaces, quotes and case ignored). Writes
dist/checks/<cc>-notes-verify.tsv: employer, found / not found / unreadable, page, evidence. No AI.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grad_pages import text_and_links  # noqa: E402
from verify_sites import fetch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def norm(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"[^a-z0-9]+", "", s)


def one(r: dict) -> tuple[str, str, str, str]:
    status, final, page = fetch(r["programme"], timeout=20)
    if status != 200 or not page:
        return r["name"], "unreadable", r["programme"], r["evidence"]
    text, _ = text_and_links(page, final)
    ev = norm(r["evidence"])
    # a sentence copied with a word or two trimmed still counts: its longest half must be on the page
    half = max(ev[: len(ev) // 2], ev[len(ev) // 2:], key=len)
    hit = ev in norm(text) or (len(half) > 25 and half in norm(text))
    return r["name"], "found" if hit else "not found", r["programme"], r["evidence"]


def main() -> int:
    cc = sys.argv[1]
    rows = []
    for f in sorted((ROOT / "dist" / "checks").glob(f"{cc}-*.out.jsonl")):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("status") == "confirmed" and r.get("notes") and r.get("evidence") and \
                    str(r.get("programme", "")).startswith("http"):
                rows.append(r)
    with cf.ThreadPoolExecutor(12) as ex:
        out = list(ex.map(one, rows))
    tally = {k: sum(o[1] == k for o in out) for k in ("found", "not found", "unreadable")}
    (ROOT / "dist" / "checks" / f"{cc}-notes-verify.tsv").write_text(
        "employer\tresult\tpage\tevidence\n" + "".join("\t".join(o) + "\n" for o in out), encoding="utf-8")
    print(f"{cc}: {len(out)} notes with evidence: {tally}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
