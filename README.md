# campus-employers

An open list of the employers that hire new graduates, starting with mainland China's 校园招聘: who they are, what kind
of employer each is, how big, where they hire, and **where and how their campus postings can be read** (the careers
site and the recruiting system behind it). Openings and closing dates are not kept here: they change daily, so a
tool reads them live from each careers site (Resume Studio scans them with no AI once the system is known).

Why: a graduate from an ordinary family knows the ten biggest names and little else. The mid-sized firms, unicorns,
SOE subsidiaries, foreign R&D centres and research institutes that hire thousands of graduates a year are invisible
unless someone already works there. This list is meant to be that someone.

## Files

- `data/cn/<sector>-NN.jsonl`: one employer per line, grouped by sector, one file per batch as it was confirmed.
- `data/cn/<sector>.todo.txt`: employers that belong in the sector and are not in it yet (a later pass adds them).
- `scripts/validate.py`: checks every file (`python scripts/validate.py`), and with `--merge` writes
  `dist/cn.json` (all sectors, duplicates merged).

## Where it stands (2026-11)

7,750 employers in 25 sectors (`dist/cn.json`), about 5,400 with a confirmed homepage and 1,958 with a confirmed
careers site; for about 1,100 of those the recruiting system is known, so Resume Studio can scan them with no AI.
Many state-owned employers' sites answer only inside mainland China and still wait for a browser pass.

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
