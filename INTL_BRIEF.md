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

## United Kingdom (`gb`)

- `nature`: `gb.company`, `gb.state` (Royal Mail is not; Network Rail, the Post Office, NatWest only while majority
  state-held, BBC, Channel 4), `gb.government` (Civil Service departments and agencies, the Bank of England, the NHS
  bodies that are not trusts, councils), `gb.research` (universities, UKRI institutes, the Met Office's science arm),
  `gb.nonprofit`. An NHS trust or health board is `gb.government` with `industry` Healthcare.
- `hq` is the city (`London`, `Edinburgh`); `cities` the UK cities it hires graduates in. `listed`: `LSE BARC`.
- Graduate intakes here are graduate schemes, summer internships (penultimate year), spring weeks and industrial
  placements (a year in industry): `hires` `internship` covers the last three. Degree apprenticeships are not
  graduate roles.
- `notes` wordings: "Right to work in the UK required"; "Sponsors Skilled Worker visas for this scheme" or "Does not
  sponsor visas" (only when certain); "Civil Service nationality rules apply" (most departments: UK, Irish,
  Commonwealth and some EU nationals); "UK nationals only (security vetting, SC/DV)"; "Accepts Graduate visa
  holders". Never guess sponsorship.

## Japan (`jp`)

- `nature`: `jp.company`, `jp.state` (Japan Post, NHK, JOGMEC, NEXI and other 独立行政法人 that hire like companies),
  `jp.government` (ministries and agencies, prefectures and cities, the Bank of Japan), `jp.research` (RIKEN, AIST,
  JAXA, universities), `jp.nonprofit`.
- `name` in its usual English or romanised form (`Toyota Motor`, `Mitsubishi Corporation`, `Nitori`); `full_name` the
  registered Japanese name (`トヨタ自動車株式会社`); `aliases` the short Japanese name (トヨタ) and the Chinese name in
  common use (丰田汽车). `hq` and `cities` in English (`Tokyo`, `Osaka`, `Nagoya`).
- Graduates are hired once a year as 新卒 (`graduate`); internships here are mostly short programmes for students
  (`internship`). `listed`: `TSE 7203`.
- `notes` wordings: "Japanese nationality required (national civil service)"; "Japanese at business level (JLPT N1)
  required"; "Hires international students on the same 新卒 schedule"; "Global (English) track open to
  international graduates". Write them only when known for this employer.
- Japan's general and specialised trading companies (総合商社, 専門商社) have a sector of their own, `trading`
  (`industry` "Trading Companies").

## Germany (`de`)

- `nature`: `de.company`, `de.state` (Deutsche Bahn, KfW, the Landesbanken, Sparkassen, city utilities
  (Stadtwerke) and other companies owned by the federal state, a Land or a city), `de.government` (federal ministries and
  agencies, the Bundesbank, Länder administrations, cities), `de.research` (Max Planck, Fraunhofer, Helmholtz and
  Leibniz institutes, universities), `de.nonprofit`.
- `name` as used (`Siemens`, `Deutsche Bank`, `BASF`); `hq` and `cities` in English (`Munich`, `Cologne`,
  `Frankfurt`). `listed`: `XETRA SIE`.
- Graduate intakes are trainee programmes (`graduate`), direct entry for graduates (`graduate`), internships and
  Werkstudent roles (`internship`), and theses written at the company (`internship`). Dual study (duales Studium)
  and Ausbildung are not graduate roles.
- `notes` wordings: "Fluent German required (C1)"; "English-language trainee programme"; "EU citizenship required
  (civil service / Beamte)"; "Security clearance required". Only when known.

## Sectors (for `gb`, `jp`, `de`)

`industry` is the label in brackets; the same label as the United States so the filter reads the same.

- `banking` (Banking & Financial Services): banks, building societies, savings banks and cooperative banks
  (Sparkassen, Volksbanken; Japan's regional banks and shinkin banks), card and payments firms.
- `finance` (Banking & Financial Services): insurers, asset and wealth managers, investment banks and brokers,
  trading firms, private equity, exchanges, fintech.
- `pro` (Professional Services): accounting and audit, strategy, management and IT consulting, law firms,
  actuarial, market research, HR consulting.
- `software` (Technology): software companies and IT services (system integrators, Japan's SIer).
- `internet` (Technology): internet platforms, e-commerce, marketplaces, games, consumer apps.
- `hardware` (Technology): semiconductors, electronics and components, telecom equipment, computers.
- `industrial` (Industrials, Aerospace & Defense): machinery, automation, electrical equipment, aerospace, defence.
- `energy` (Energy, Utilities & Materials): oil and gas, power and utilities, water, chemicals, steel and metals,
  mining, building materials, paper.
- `built` (Real Estate, Construction & Engineering): construction, real estate, engineering consultancies,
  architecture, housing.
- `transport` (Transportation & Automotive): carmakers and suppliers, airlines, rail, shipping, logistics, airports.
- `consumer` (Consumer & Retail): food and drink, household goods, fashion and luxury, retail, hospitality, travel.
- `healthcare` (Healthcare & Life Sciences): hospitals and health services (NHS trusts, German hospital groups,
  Japanese hospital groups), care providers, health insurers' care arms.
- `lifesci` (Healthcare & Life Sciences): pharmaceuticals, biotech, medical devices, diagnostics, CROs.
- `media` (Media, Telecom & Entertainment): telecom operators, broadcasting, publishing, advertising and PR,
  entertainment.
- `government` (Government & Research): national government departments and agencies, regulators, the central
  bank, local government, the armed forces as an employer.
- `research` (Government & Research): universities and public research bodies.
- `nonprofit` (Nonprofit & Education): charities, NGOs, foundations, think tanks, international organisations'
  offices, schools that hire graduates (Teach First).
- `trading` (Trading Companies, Japan only): sogo shosha and specialised trading houses.

## What not to do

- Don't invent an address, a ticker, a headcount or a visa rule. Empty is right; wrong is harmful.
- Don't copy a paid or private list (e.g. a ranking's paywalled table). Your own knowledge and public pages only.
- Don't add employers outside your country and sector (another agent has them), except a subsidiary of yours.
- Don't stop at the famous names.
