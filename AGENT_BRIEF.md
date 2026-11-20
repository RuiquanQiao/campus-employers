# Brief for an agent adding employers (read all of it before starting)

You are building one sector of an open database of the employers that hire new graduates in mainland China
(校园招聘). The person using it is a graduate who only knows the biggest names; the database exists to show every
serious employer in the sector, the mid-sized and lesser-known ones above all, with where to apply. Be thorough: a
sector half done is the failure this work exists to prevent. Never be satisfied with the famous names alone.

## What to do (list-only pass: no web search)

This pass lists employers; it does not look up careers sites. A script later opens each `website`, follows its own
招聘 / 加入我们 / 校园招聘 links to the careers site, and Resume Studio tells which recruiting system runs it. So:

1. **Don't use WebSearch or WebFetch.** Work from what you know. Search is shared by many agents and runs out.
2. **List everything first**: every serious employer in your sector that hires graduates in China: leaders, the second
   and third tier, unicorns and fast-growing firms, listed mid-caps, subsidiaries that run their own 校招. "Serious"
   means a real, operating employer of some size or standing that a graduate would not regret joining: no shell
   companies, no tiny agencies, no 外包派遣 shops posing as employers. If your sector has 300 serious employers, the
   list should have close to 300. Never stop at the famous names: the mid-sized and lesser-known ones are why this
   exists.
3. **Every line carries `website`**: the employer's official homepage (`https://www.sany.com.cn`), which you usually
   know for certain. `""` only when you truly don't know it. Never a news page, an encyclopedia or a job board.
4. `campus_site` stays `""` and `checked` stays `""` unless you know the careers address for certain (the big names:
   `https://jobs.bytedance.com/campus`). If you believe you know it but aren't sure, put it in `site_candidates`
   (a list, best first) instead; a script checks each. Never a guess in `campus_site`.
5. Fill the other fields from what you know, and only what you are sure of. A fact you aren't sure of stays `""`.
   `scale`, `listed` and `funding` are facts with a year, never a grade or an opinion.
6. **Write each batch of 30 as soon as it is listed** to its own file, `data/cn/<sector>-NN.jsonl` (NN = 01, 02, …,
   continuing after any file of your sector already there), one JSON object per line, UTF-8, **with the Write tool**.
   Never rewrite a file you didn't write in this pass. Don't write generator scripts; if you must, keep them in your
   own folder (named after your sector) under the scratchpad, never a shared name like `gen.py`.
7. **At the end**, write `data/cn/<sector>.todo.txt` (one line per employer that belongs and isn't written, if any),
   run `python scripts/validate.py` from `E:\Forge\campus-employers` (in PowerShell:
   `cd E:\Forge\campus-employers; ..\resume-studio\.venv\Scripts\python.exe scripts\validate.py`) and fix every
   problem it prints in your own files.
8. **Report** in a few lines: how many employers written, how many with a `website`, the files, anything left.

## One line

```json
{"name": "宁德时代", "full_name": "宁德时代新能源科技股份有限公司", "aliases": ["CATL"], "nature": "cn.private", "industry": "新能源", "sub": "动力电池", "parent": "", "hq": "宁德", "cities": ["宁德", "上海", "溧阳"], "listed": "深交所 300750", "scale": "员工约 13 万人（2024 年报）", "funding": "", "campus_site": "https://catl.zhiye.com/campus", "system": "北森", "hires": ["校招", "实习"], "roles": ["研发工程师", "工艺工程师", "质量工程师"], "notes": "", "sources": ["https://catl.zhiye.com/campus"], "checked": "2026-11", "site_candidates": [], "website": "https://www.catl.com"}
```

Every field is always present (empty `""` or `[]` when not known), plus `site_candidates` (a list, `[]` when
`campus_site` is confirmed) and `website`. The rules:

- `name`: the name people use. `full_name`: the registered name if you know it.
- `nature`, exactly one of:
  - `cn.central_soe` 央企: a group on 国资委's list of 中央企业, or a subsidiary of one;
  - `cn.state_finance` 国有金融: a bank, insurer, broker or fund controlled by the state (中央汇金, 财政部, a local
    government's finance arm): 工农中建交, 国开行, 招商银行 (招商局 controls it), 中信证券…;
  - `cn.local_soe` 地方国企: controlled by a province's or city's 国资委;
  - `cn.private` 民企: privately controlled Chinese company, listed or not;
  - `cn.foreign` 外企 / 合资: a foreign company's China entity, or a joint venture with a foreign partner;
  - `cn.public` 事业单位; `cn.university` 高校 / 科研院所 (中科院's institutes, 国家实验室); `cn.civil` 党政机关.
- `industry`: the sector's name you were given; `sub`: its line within it (动力电池, 模拟芯片, 城商行…).
- `parent`: the group, for a subsidiary listed in its own right (it hires on its own site or in its own 校招).
- `hq`: a city in Chinese (北京, 深圳); `cities`: where it hires graduates, at most 8.
- `hires`: any of 校招, 实习, 社招. `roles`: up to 6 graduate roles *this* employer is known to hire for, in
  Chinese. Never a generic list copied across a sub-sector: `[]` is right when you don't know this one's.
- `notes`: only facts that decide who can apply (只招中国籍, 需应届生身份, 硕士及以上, 需本地户口).
- `sources`: the addresses you read (the careers site counts). `checked`: `"2026-11"` when you confirmed the careers
  site this time, else `""`.
- A group and its subsidiaries: one line for the group, plus one line for each subsidiary that runs a 校招 of its own
  (with `parent` set). Don't list every branch office.

## What not to do

- Don't invent an address, a code, a headcount or a funding round. Empty is right; wrong is harmful.
- Don't copy a paid or private summary table. Your own knowledge and public pages only.
- Don't add employers outside your sector (another agent has them), except a subsidiary of yours.
- Don't stop at the famous names. If your sector has 300 serious employers, the list should have close to 300.
