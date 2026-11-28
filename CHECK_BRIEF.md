# Brief for an agent checking employers' graduate pages (read all of it before starting)

You are given one batch file, `dist/checks/<cc>-NN.in.jsonl`: one employer per line with `name`, `website`,
`campus_site` and `site_candidates`. For each employer, find its own page for graduates and interns and read
from it **who may apply**. The people using this are graduates, many of them international students; whether
they are allowed to apply at all is the fact they most need and least often find.

## For each employer

0. A script has already opened each employer's careers and graduate pages: `dist/checks/<cc>-NN.pages.jsonl` (same
   NN; if it doesn't exist yet, make it: `cd E:\Forge\campus-employers; ..\resume-studio\.venv\Scripts\python.exe
   scripts\grad_pages.py dist\checks\<cc>-NN.in.jsonl` in PowerShell, about a minute) gives, per employer, the pages read with their HTTP `status`, the sentences that `mention` a graduate or intern
   intake and the `facts` sentences about who may apply. Read it first; it is the main source. Its sentences are
   matched by pattern, so many are noise: a credit card's eligibility, a "Visa" card, community sponsorship, a
   statement about **another country's** programme (UK, US, Singapore…). Use only sentences about this employer's
   graduate or intern intake in the country you are checking.
1. When the pages file has no graduate mention for an employer, **always** look further; never skip this step:
   WebFetch `campus_site`, then `site_candidates`, then the careers link on `website`, following at most two links
   (Graduates, Internships, Eligibility, FAQ); at most 3 fetches per employer. If still nothing, one WebSearch
   (`<name> graduate program <country>`); only results on the employer's own site or its recruiting system count.
   `careers_only` and `unreachable` are written only after this step was tried.
   - A global firm's early-careers site counts as this country's when it lists a programme or role located in this
     country (e.g. "Sydney", "Australia" in the programme list or a job posting): that is `confirmed`. A search
     result that is such a posting on the firm's own site also counts, with `programme` set to it.
2. Write one line to `dist/checks/<cc>-NN.out.jsonl` (same NN), with the Write tool, every 20 employers:

```json
{"name": "Commonwealth Bank", "status": "confirmed", "programme": "https://www.commbank.com.au/about-us/careers/graduate-and-intern-programs.html", "hires": ["graduate", "internship"], "notes": "Australian or New Zealand citizens and Australian permanent residents only", "evidence": "You must be an Australian or New Zealand citizen or an Australian permanent resident"}
```

- `name`: exactly as in the input line.
- `status`: `confirmed` (a page for graduates or interns in this country was read), `no_intake` (the careers site
  states there is no graduate or intern intake), `careers_only` (the careers site was read and mentions no graduate,
  intern or vacation programme for this country), `unreachable` (no careers page could be opened or found).
- `programme`: the address of the page read; `""` when none.
- `hires`: what that page offers: `graduate`, `internship`, `experienced`; `[]` when not read.
- `notes`: **only what the page states** about who may apply, in one plain sentence, using these wordings where
  they fit:
  - Australia: "Australian citizens only"; "Australian citizens and permanent residents only"; "Australian or New
    Zealand citizens and Australian permanent residents only"; "Open to international students with full working
    rights"; "Security clearance required (Baseline / NV1 / NV2)".
  - United States: "US citizens only"; "US citizens and permanent residents only"; "Does not sponsor work visas";
    "Sponsors work visas for this programme" (only when the page says so); "Security clearance required".
  - United Kingdom: "Right to work in the UK required"; "Sponsors Skilled Worker visas for this scheme" / "Does not
    sponsor visas" (only when the page says so); "Civil Service nationality rules apply"; "UK nationals only (security
    vetting, SC/DV)"; "Accepts Graduate visa holders". Graduate schemes, summer internships, spring weeks and
    industrial placements all count as a programme, and so do graduate-entry training schemes (Step Up to Social
    Work, Frontline, Teach First, NHS graduate management). Supported internships for young people with an EHCP and
    degree apprenticeships do not. An NHS preceptorship or Flying Start programme for newly qualified nurses,
    midwives, paramedics or allied health staff counts as a graduate programme (`hires: ["graduate"]`); a medical
    student's elective does not.
  - Japan: "Japanese nationality required"; "Japanese at business level (JLPT N1) required"; "International students
    welcome on the same 新卒 schedule"; "Global (English) track open to international graduates". A 新卒採用 page
    (募集要項, 初任給, エントリー) or an インターンシップ page counts as a programme. Quote the Japanese sentence as is.
  - Germany: "Fluent German required (C1)"; "English-language trainee programme"; "EU citizenship required";
    "Work permit for Germany required"; "Security clearance required". A trainee programme, a direct-entry page for
    graduates (Direkteinstieg, Berufseinstieg), a Praktikum, Werkstudent or Abschlussarbeit page counts. Quote the
    German sentence as is.
  - Add a degree or timing condition only when it decides who can apply ("Final-year students or graduated within
    the last two years").
  `""` when the page says nothing about it. Never infer from the type of employer.
- `evidence`: the sentence the notes come from, copied, at most 25 words; `""` when `notes` is empty. It must be a
  sentence read on the page itself (the pages file or a WebFetch of the page asked to quote it word for word), never a
  search result's snippet or a summary; when only a summary says it, leave `notes` and `evidence` empty.

## Rules

- Never touch any file except your own `.out.jsonl`. Never edit `data/`.
- Every employer in the input gets exactly one output line, in the input's order.
- A page that is plainly another employer's, a job board, or a recruitment agency doesn't count.
- Report at the end in a few lines: how many confirmed / no_intake / careers_only / unreachable, how many with
  notes, and how many employers got the step-1 look further.
