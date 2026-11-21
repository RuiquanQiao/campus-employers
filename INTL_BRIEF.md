# Brief for an agent adding employers outside mainland China (read all of it before starting)

You are building one part of an open database of the employers that hire new graduates: graduate programmes,
internships and entry-level roles. You are given a **country** (its two-letter code, e.g. `au`) and a **sector**.
The people using it are graduates, many of them international students, who know only the biggest names; the
database exists to show every serious employer in the sector, the mid-sized and lesser-known ones above all, and
whether someone without citizenship can apply. Be thorough: a sector half done is the failure this work exists to
prevent.

## What to do (list-only pass: no web search)

1. **Don't use WebSearch or WebFetch.** Work from what you know. Search is shared and runs out.
2. **List everything first**: every serious employer in the sector that hires graduates in that country: the
   leaders, the second and third tier, mid-caps, fast-growing private firms, foreign firms with a real graduate
   intake there, government bodies with a graduate programme (for the government sector). "Serious" means a real,
   operating employer of some size or standing; no shell companies, recruitment agencies or labour-hire firms. If
   the sector has 250 such employers, the list should have close to 250.
3. **Every line carries `website`**, the employer's official homepage in that country
   (`https://www.commbank.com.au`), which you usually know. `""` only when you truly don't know it.
4. `campus_site` is the page where its graduate / early-careers roles are listed (`https://www.commbank.com.au/
   graduate`). Write it only when you know it for certain; a believed one goes in `site_candidates` (best first).
   `checked` stays `""`. A script opens every homepage and finds the careers page later.
5. Write each batch of 30 as soon as it is listed to `data/<cc>/<sector>-NN.jsonl` (NN = 01, 02, …, after any file
   of your sector already there), one JSON object per line, UTF-8, **with the Write tool**. Never touch a file you
   didn't write. No generator scripts in the repository; if you need one, keep it in your own folder under the
   scratchpad, named after your country and sector.
6. At the end write `data/<cc>/<sector>.todo.txt` (employers that belong and aren't written, if any), run
   `cd E:\Forge\campus-employers; ..\resume-studio\.venv\Scripts\python.exe scripts\validate.py` in PowerShell, and
   fix every problem it prints in your own files.
7. **Report** in a few lines: how many written, how many with a `website`, how many with `notes`, the files.

## One line

```json
{"name": "Commonwealth Bank", "full_name": "Commonwealth Bank of Australia", "aliases": ["CBA", "CommBank", "澳洲联邦银行"], "nature": "au.company", "industry": "Banking & Financial Services", "sub": "Major bank", "parent": "", "hq": "Sydney", "cities": ["Sydney", "Melbourne", "Brisbane", "Perth"], "listed": "ASX CBA", "scale": "about 49,000 staff (2024 annual report)", "funding": "", "campus_site": "", "system": "", "hires": ["graduate", "internship"], "roles": ["Technology graduate", "Data & analytics graduate", "Business graduate"], "notes": "Graduate programme open to Australian and New Zealand citizens and Australian permanent residents", "sources": [], "checked": "", "site_candidates": ["https://www.commbank.com.au/about-us/careers/graduate-and-intern-programs.html"], "website": "https://www.commbank.com.au"}
```

Every field is always present (`""` or `[]` when not known). The rules:

- `name`: the name people use, in English (or the country's usual Latin spelling). `full_name`: the registered name.
- `aliases`: abbreviations, former names, and **the Chinese name when one is in common use** (必和必拓, 星展银行,
  汇丰, 德勤): many users search in Chinese.
- `nature`, exactly one of (`<cc>` is the country code you were given):
  - `<cc>.company`: a private or listed company, including a foreign company's local arm;
  - `<cc>.state`: a company owned by the state (Australia Post, Temasek-linked firms such as SingPost when majority
    held, Japan Post);
  - `<cc>.government`: a government department, agency, regulator or the public service as an employer
    (Australian Public Service departments, the UK Civil Service Fast Stream, a central bank);
  - `<cc>.research`: a university or public research body hiring graduates (CSIRO, A*STAR);
  - `<cc>.nonprofit`: a charity, NGO or international organisation office.
- `industry`: the sector's name you were given; `sub`: the line within it (Major bank, Iron ore, Strategy
  consulting…).
- `parent`: the group, for a subsidiary that hires on its own.
- `hq`: the city of its head office in that country, in English; `cities`: where it hires graduates there, at most 8.
- `hires`: any of `graduate` (a graduate programme or new-graduate roles), `internship` (including summer / vacation
  programmes), `experienced`.
- `roles`: up to 6 graduate roles *this* employer is known to hire for, in English. Never a generic list copied
  across a sub-sector: `[]` when you don't know this one's.
- `notes`: **only facts that decide who can apply**, above all citizenship and visa: "Australian citizens only (APS
  requirement)", "Open to international students with full work rights", "Requires Singapore citizenship or PR",
  "Security clearance required (NV1)". Write it only when you know it; it is the most useful field for an
  international student, and a wrong one is harmful.
- `scale`, `listed`, `funding`: facts with a year, never a grade ("ASX BHP", "about 80,000 staff (2024)").
- `sources`: addresses you read (none in this pass: `[]`). `system`: the recruiting system only when you are sure
  (Workday, PageUp, SuccessFactors, Oracle, Greenhouse, Lever, Avature, Eightfold…), else `""`.
- A group and its subsidiaries: one line for the group, plus one per subsidiary that runs its own graduate intake.

## Adding to a country already listed

When your country already has employers (`dist/<cc>.json`), you are given an **area** (e.g. hospitals and health
services) and the existing `industry` name your lines carry, so the page's industry filter stays the same. First read
every `name` and `aliases` in `dist/<cc>.json` and write **only employers not in it**; the file prefix you are given
(`data/<cc>/<prefix>-NN.jsonl`) is yours alone. The aim is the employers a graduate would never hear of: public
health services, councils, water and power utilities, mid-tier firms, regional employers, foreign firms' local arms.
A group whose units recruit separately (a state's local health districts, a university's campuses only if they
recruit apart) gets one line per unit that runs its own graduate intake.

## United States

- `nature`: `us.company`, `us.state` (rare: Amtrak, the Tennessee Valley Authority, USPS), `us.government`
  (federal, state and city agencies, the Federal Reserve banks), `us.research` (national laboratories, universities,
  FFRDCs such as MITRE), `us.nonprofit`.
- `hq` is the city of the head office (`New York`, `Seattle`); `cities` at most 8 US cities it hires graduates in.
- `listed`: `NYSE JPM`, `Nasdaq AAPL`.
- `notes` matter most here for an international student: write them only when certain, e.g. "US citizenship required
  (security clearance)", "Federal Pathways programme: US citizens only", "Does not sponsor work visas for
  graduate roles". Never guess whether a company sponsors H-1B.
- Campus pages are often on Workday (`*.myworkdayjobs.com`), Greenhouse, Lever, Eightfold, Avature, iCIMS or Phenom;
  write `system` only when sure.

## What not to do

- Don't invent an address, a ticker, a headcount or a visa rule. Empty is right; wrong is harmful.
- Don't copy a paid or private list (e.g. a ranking's paywalled table). Your own knowledge and public pages only.
- Don't add employers outside your country and sector (another agent has them), except a subsidiary of yours.
- Don't stop at the famous names.
