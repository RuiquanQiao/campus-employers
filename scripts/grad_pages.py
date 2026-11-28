"""Read each employer's graduate pages before an agent does (CHECK_BRIEF.md), so the agent reads sentences, not sites.

    python scripts/grad_pages.py dist/checks/au-01.in.jsonl [more batch files…]

For each employer in a batch: its careers site, the candidates and the homepage are opened, the links that lead to
graduate / intern / early-careers / eligibility pages are followed (up to five, on the employer's own domain or a
recruiting system's), and from every page read the sentences that say who may apply (citizen, permanent resident,
working rights, visa, clearance, registration) and the ones that mention a graduate or intern intake are kept.
Written next to the batch as <batch>.pages.jsonl, one line per employer:
    {"name", "pages": [{"url", "status", "grad": n, "facts": [...], "mentions": [...]}]}
No AI, no search.
"""
from __future__ import annotations

import concurrent.futures as cf
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_sites import fetch  # noqa: E402

GRAD_LINK = re.compile(r"graduat|intern(ship)?s?\b|early[-_ ]?career|student|vacation|cadet|summer|entry[-_ ]?level|"
                       r"eligib|campus|university|emerging[-_ ]?talent|future[-_ ]?talent|trainee|new[-_ ]?grad|"
                       r"spring[-_ ]?week|placement|"
                       # Japan: 新卒 / 新卒採用 / インターンシップ / 学生 / 募集要項; Germany: Absolventen, Berufseinstieg,
                       # Praktikum, Werkstudent, Studierende, Einstieg, Abschlussarbeit
                       r"shinsotsu|recruit/new|fresh|新卒|インターン|学生|募集要項|採用情報|"
                       r"absolvent|berufseinst|einstieg|praktik|werkstudent|studierende|studenten|abschlussarbeit|"
                       r"karriere|studium", re.I)
CAREERS_LINK = re.compile(r"career|jobs?\b|join[-_ ]?us|work[-_ ]?(with|for)[-_ ]?us|vacanc|employment|recruit", re.I)
FACT = re.compile(r"citizen|permanent resident|working rights|work rights|right to work|"
                  r"visa (status|holder|sponsor|requirement|condition|restriction)|(student|work|working|graduate|"
                  r"temporary|subclass \d+) visa|sponsor(ship)? (for|of) (a )?(work )?visa|visa sponsorship|"
                  r"eligib\w* (to|for) (apply|our|the|this) (graduate|intern|program|role|position)|to be eligible|"
                  r"eligibility (criteria|requirement)|security clearance|baseline clearance|\bNV ?[12]\b|AHPRA|"
                  r"work authori[sz]ation|authori[sz]ed to work|US person|green card|"
                  r"right to work in the UK|skilled worker visa|graduate visa|visa sponsor|sponsor (a )?visa|nationality rules|"
                  r"国籍|日本国籍|日本語能力|JLPT|留学生|外国籍|在留資格|"
                  r"Staatsangehörigkeit|Arbeitserlaubnis|Aufenthaltstitel|Deutschkenntnisse|EU-Bürger|"
                  r"Sicherheitsüberprüfung|verhandlungssicher", re.I)
MENTION = re.compile(r"graduate (program|programme|role|intake|opportunit)|internship|summer (intern|analyst|vacation)|"
                     r"vacation (program|programme|placement)|early careers|new grad|cadetship|graduate scheme|"
                     r"spring week|industrial placement|placement year|training contract|"
                     r"新卒採用|新卒|インターンシップ|募集要項|初任給|"
                     r"Trainee(programm)?|Traineeprogramm|Direkteinstieg|Praktikum|Werkstudent|Abschlussarbeit|"
                     r"Absolventen|Berufseinstieg", re.I)
ATS = re.compile(r"myworkdayjobs|pageuppeople|successfactors|oraclecloud|taleo|greenhouse|lever\.co|avature|"
                 r"eightfold|smartrecruiters|icims|workable|ashbyhq|brassring|jobvite|gradconnection|"
                 r"applynow|livehire|elmotalent|bigredsky|springboard|phenom|teamtailor|recruitee", re.I)
SAY = re.compile(r"(?<=[.!?])\s+")
MAX_PAGES = 7
GUESSES = ["/careers/graduates", "/careers/graduate-program", "/graduates", "/graduate-program", "/early-careers",
           "/careers/early-careers", "/careers/students", "/students", "/careers/internships", "/internships",
           "/careers/graduate-programs", "/graduate-programs", "/careers/university-students", "/university"]


def text_and_links(page: str, base: str) -> tuple[str, list[tuple[str, str]]]:
    links = []
    for m in re.finditer(r"<a\b[^>]*?href\s*=\s*[\"']([^\"'#]+)[\"'][^>]*>(.*?)</a>", page, re.S | re.I):
        label = re.sub(r"<[^>]+>|\s+", " ", m.group(2)).strip()
        try:
            links.append((urljoin(base, html.unescape(m.group(1))), label))
        except ValueError:
            continue
    body = re.sub(r"<(script|style|noscript|svg)\b.*?</\1>", " ", page, flags=re.S | re.I)
    body = re.sub(r"<(br|p|li|h[1-6]|div|tr|section)\b[^>]*>", ". ", body, flags=re.I)
    body = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return re.sub(r"\s+", " ", body), links


def domain(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    parts = host.split(".")
    return ".".join(parts[-3:]) if len(parts) > 2 and parts[-2] in ("com", "gov", "org", "edu", "net", "co") \
        else ".".join(parts[-2:])


def sentences(text: str, pat: re.Pattern, n: int) -> list[str]:
    out = []
    for s in SAY.split(text):
        s = s.strip(" .")
        if 20 < len(s) < 400 and pat.search(s) and s not in out:
            out.append(s)
            if len(out) >= n:
                break
    return out


def one(emp: dict) -> dict:
    home = emp.get("website") or ""
    own = {domain(u) for u in [home, emp.get("campus_site") or "", *(emp.get("site_candidates") or [])] if u}
    queue = [u for u in [emp.get("campus_site"), *(emp.get("site_candidates") or []), home] if u]
    seen, pages = set(), []
    while queue and len(seen) < MAX_PAGES:
        url = queue.pop(0)
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        status, final, page = fetch(url, timeout=15)
        if status != 200 or not page:
            pages.append({"url": url, "status": status, "grad": 0, "facts": [], "mentions": []})
            continue
        text, links = text_and_links(page, final)
        mentions = sentences(text, MENTION, 5)
        pages.append({"url": final, "status": status, "grad": len(MENTION.findall(text)),
                      "facts": sentences(text, FACT, 10), "mentions": mentions})
        grad, careers = [], []
        for link, label in links:
            if not link.startswith("http") or (domain(link) not in own and not ATS.search(link)):
                continue
            if GRAD_LINK.search(label) or GRAD_LINK.search(urlsplit(link).path):
                grad.append(link)
            elif CAREERS_LINK.search(label) or CAREERS_LINK.search(urlsplit(link).path):
                careers.append(link)
        # graduate pages first, then a careers page when nothing graduate-like has been found yet
        queue = list(dict.fromkeys(grad[:5] + queue + ([] if any(p["grad"] for p in pages) else careers[:2])))
    # nothing graduate-like reached by links: try the addresses graduate pages usually have on the homepage's site
    if home and not any(p["mentions"] for p in pages):
        root = "{0.scheme}://{0.netloc}".format(urlsplit(home))
        for path in GUESSES:
            url = root + path
            if url.rstrip("/").lower() in seen:
                continue
            seen.add(url.rstrip("/").lower())
            status, final, page = fetch(url, timeout=10)
            if status != 200 or not page:
                continue
            text, _ = text_and_links(page, final)
            mentions = sentences(text, MENTION, 5)
            if mentions:
                pages.append({"url": final, "status": status, "grad": len(MENTION.findall(text)),
                              "facts": sentences(text, FACT, 10), "mentions": mentions})
                break
    keep = [p for p in pages if p["facts"] or p["mentions"]] or pages[:3]
    return {"name": emp["name"], "pages": keep}


def main() -> int:
    for arg in sys.argv[1:]:
        batch = Path(arg)
        emps = [json.loads(x) for x in batch.read_text(encoding="utf-8").splitlines() if x.strip()]
        with cf.ThreadPoolExecutor(16) as ex:
            results = list(ex.map(one, emps))
        out = batch.with_name(batch.name.replace(".in.jsonl", ".pages.jsonl"))
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results), encoding="utf-8")
        found = sum(any(p["mentions"] for p in r["pages"]) for r in results)
        facts = sum(any(p["facts"] for p in r["pages"]) for r in results)
        print(f"{batch.name}: {len(emps)} employers, {found} with a graduate mention, {facts} with eligibility sentences")
    return 0


if __name__ == "__main__":
    sys.exit(main())
