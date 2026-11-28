# campus-employers

An open list of the employers that hire new graduates, starting with mainland China's 校园招聘: who they are, what kind
of employer each is, how big, where they hire, and **where and how their campus postings can be read** (the careers
site and the recruiting system behind it). Openings and closing dates are not kept here: they change daily, so a
tool reads them live from each careers site (Resume Studio scans them with no AI once the system is known).

Why: a graduate from an ordinary family knows the ten biggest names and little else. The mid-sized firms, unicorns,
SOE subsidiaries, foreign R&D centres and research institutes that hire thousands of graduates a year are invisible
unless someone already works there. This list is meant to be that someone.

**Browse it:** https://ruiquanqiao.github.io/campus-employers/ (search, filter by country, industry and type).

## Files

- `data/<country>/<sector>-NN.jsonl`: one employer per line, grouped by sector, one file per batch as it was
  confirmed. `cn` is mainland China; other countries use their two-letter code (`au`, `sg`, `hk`…) and are listed
  by `INTL_BRIEF.md`, with `notes` saying who may apply (citizenship, work rights).
- `data/<country>/<sector>.todo.txt`: employers that belong in the sector and are not in it yet.
- `scripts/validate.py`: checks every file (`python scripts/validate.py`), and with `--merge` writes
  `dist/<country>.json` (all sectors, duplicates merged). `scripts/build_site.py` then writes the browsing page's
  data (`docs/data/`); the page itself is `docs/index.html`, served by GitHub Pages.

## Where it stands (2026-11)

| Where | Employers | Careers site confirmed | Recruiting system known |
|---|---|---|---|
| Mainland China (`cn`) | 7,750 | 1,973 | 1,074 |
| Australia (`au`) | 3,811 | 2,233 | 444 |
| United States (`us`) | 5,189 | 4,367 | 1,319 |
| Singapore (`sg`) | 588 | 367 | 101 |
| Hong Kong (`hk`) | 391 | 180 | 45 |

Many state-owned employers' sites in mainland China answer only from inside it and still wait for a browser pass.

**Who may apply.** Outside China, `notes` says who may apply (citizenship, permanent residency, work rights). For
Australia each employer's graduate page was read (`CHECK_BRIEF.md`, then a second look described below): 960
employers have their graduate or intern programme confirmed from their own site, 324 of them with a rule the page
states, quoted in `dist/checks/au-*.out.jsonl`; `scripts/verify_notes.py` reopened each page and found the quoted
sentence on 267 of 326, 26 could not be reopened, and on 33 it was not found (pages that build their text in the
browser). For the United States the same checks found the programme on the employer's own site for 3,239 employers,
473 of them with a rule the page states (most often US citizens only, or no work-visa sponsorship); the quoted
sentence was found again on 271 of 479 pages, 101 could not be reopened, and on 107 it was not found (pages built in
the browser, and sentences an agent took from a search result's summary rather than the page). Each is listed in
`dist/checks/<cc>-notes-verify.tsv`.
The United Kingdom, Japan and Germany come next.

How the check runs: `scripts/checks.py split <cc>` cuts a country into batches; `scripts/grad_pages.py` opens each
employer's careers and graduate pages with no AI and keeps the sentences about an intake and about eligibility; an
agent decides from those and from the employer's own pages; `scripts/checks.py apply <cc>` writes only confirmed
results from the employer's own site (a job board's listing is not taken).

The employers the first check found no programme for get a second look, cheapest first:
`scripts/ats_check.py <cc>` reads the job list of each one's recruiting system (Workday, Greenhouse, Oracle,
SuccessFactors and some 150 more, through the career-ops providers Resume Studio's scan uses) and keeps a current
intern or graduate posting in the country, with no AI; an agent then marks from what it knows which of the rest run
a programme (`FLAG_BRIEF.md`, `scripts/flag_lists.py`), and only those are looked for again on their own sites
(`RECHECK_BRIEF.md`, `scripts/checks.py recheck`). A page about an intake of 2023 or earlier is not taken, and a later
check never undoes a confirmation. Sites that answer only a browser (Queensland Health, several federal agencies)
were read in one (`dist/checks/au-browser.out.jsonl`). Takeovers and closures the agents recalled wait in
`dist/search/<cc>-leads.tsv` until a search confirms them; those confirmed are merged or removed by
`scripts/apply_changes.py --cc <cc>` and listed with why in `dist/removed-<cc>.tsv`.

## How it is built

Three steps, each with the cheapest tool that does it; only the first uses AI.

1. **List the employers** (`AGENT_BRIEF.md`): an agent per sector writes every serious employer it knows, with its
   homepage (`website`), and no web search. Homepages it isn't sure of are guessed separately (`GUESS_BRIEF.md`,
   `data/cn/<sector>.guesses.tsv`) and `scripts/check_websites.py` keeps a guess only when the page it opens names
   the employer. `scripts/apply_websites.py` merges a sector's known homepages (`<sector>.websites.tsv`).
2. **Find the careers site** (`scripts/find_sites.py`): each homepage is opened as a visitor in mainland China would
   see it, its 校园招聘 / 招聘 / 加入我们 links are followed one step, and the recruiting addresses found are ranked.
3. **Tell the system** (same script): each candidate is asked by its address (zhiye.com is 北森 …) and by Resume
   Studio's own detectors (`jobhunt/beisen.py`, `hotjob.py`, `feishu.py`, `iguopin.py`, `alitalent.py`, imported
   from a Resume Studio checkout beside this one), the same code its scan uses. A site a detector reads is one
   Resume Studio can scan with no AI; `system` says which.

Homepages neither the listing agent nor a guess found are searched for, one employer at a time (`SEARCH_BRIEF.md`,
`scripts/search_batches.py`, results in `data/cn/<sector>.search.tsv`), and checked the same way; a searched
homepage that only can't be reached from outside mainland China is kept. What the searches turned up about the
employer itself (closed, merged, renamed, a wrong parent or headquarters) is noted in `dist/search/changes.tsv`,
turned into one action per line in `dist/search/actions.tsv` (unconfirmed notes are skipped), and applied by
`scripts/apply_changes.py`; every employer removed or merged is listed with why in `dist/removed.tsv`.

What none of these reach (an anti-bot check, a site that answers only inside mainland China) is listed in
`dist/find-report-<sector>.tsv` for a browser pass. `scripts/coverage.py` prints the counts per sector;
`scripts/tidy.py` empties `roles` lists copied across a sub-sector.

## One employer

```json
{"name": "宁德时代", "full_name": "宁德时代新能源科技股份有限公司", "aliases": ["CATL"],
 "nature": "cn.private", "industry": "新能源", "sub": "动力电池", "parent": "",
 "hq": "宁德", "cities": ["宁德", "上海", "溧阳"],
 "listed": "深交所 300750", "scale": "员工约 13 万人（2024 年报）", "funding": "",
 "campus_site": "https://catl.zhiye.com/campus", "system": "北森",
 "hires": ["校招", "实习"], "roles": ["研发工程师", "工艺工程师", "质量工程师"],
 "notes": "", "sources": ["https://catl.zhiye.com/campus"], "checked": "2026-11"}
```

| Field | What it holds |
|---|---|
| `name` | the name people use (宁德时代, not the registered name) |
| `full_name` | the registered name, when known |
| `aliases` | other names it goes by: English name, old name, abbreviation |
| `nature` | one of `cn.central_soe` (央企), `cn.local_soe` (地方国企), `cn.state_finance` (国有金融), `cn.private` (民企), `cn.foreign` (外企 / 合资), `cn.public` (事业单位), `cn.university` (高校 / 科研院所), `cn.civil` (党政机关) |
| `industry`, `sub` | the sector and the line of business within it |
| `parent` | the group it belongs to, for a subsidiary that hires on its own (国家电网 → 国网江苏省电力有限公司) |
| `hq`, `cities` | headquarters, and the cities it hires graduates in |
| `listed`, `scale`, `funding` | facts with a year, never a grade: the exchange and code, headcount or revenue, the last round |
| `campus_site` | the page where its campus roles are listed and applied for; `""` when not found |
| `system` | the recruiting system behind it: 北森, Moka, 飞书, HotJob, 智联, 国聘, 自建, … `""` when not known |
| `hires`, `roles` | 校招 / 实习 / 社招, and the roles it typically hires graduates for |
| `notes` | facts that decide who can apply (只招中国籍, 需本地户口, 硕士起) |
| `sources` | where each fact was read |
| `checked` | the month the careers site was last confirmed |
| `website` | the employer's official homepage, where the careers site is looked for |
| `site_candidates` | careers addresses found or believed but not yet confirmed, best first |

Nothing is guessed: a field not confirmed is empty. A careers site is only written when found on the company's own
domain or on a recruiting system's domain that names the company.
