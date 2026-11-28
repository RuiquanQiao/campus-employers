# Brief for the second look at an employer's graduate pages (read all of it before starting)

The first pass (`CHECK_BRIEF.md`) found no graduate or intern programme for the employers in your batch,
`dist/checks/<cc>-rNN.in.jsonl`. Many of them do run one: the first pass read only the pages a script could
open, and large employers often keep their programme on an early-careers site, a recruiting system (Workday,
SuccessFactors, Greenhouse, Lever, PageUp, Oracle, Avature, Eightfold…) or a page the careers home does not link.
Your job is to find it when it exists, and to be sure when it does not.

Each input line has `name`, `website`, `campus_site`, `site_candidates`, and what the first pass wrote:
`first_pass` (`careers_only`, `unreachable` or `no_intake`) and `first_page` (the page it read, maybe `""`).

## For each employer, in this order

Web searches are scarce (all agents together share about 200 in a turn); page fetches are not. So open pages first
and search only when that fails.

1. **Fetch first.** WebFetch the careers home (`campus_site`, else `first_page`, else the careers link on
   `website`) and look for links named Graduates, Students, Early careers, Internships, Vacation, Cadetship,
   University; follow them (at most two levels). If the careers home has no such link, try one or two usual
   addresses on the same site (`/graduates`, `/early-careers`, `/students`, `/careers/graduate-program`).
2. **Search only when step 1 found nothing**: one WebSearch `<name> graduate program <country>` (for the United
   States: `<name> internship program`). When the results show a programme page on the employer's own site or
   its recruiting system (e.g. `<employer>.wd3.myworkdayjobs.com`, `<employer>.pageuppeople.com`, Greenhouse,
   Lever), **open it**: that page decides, even when earlier fetches used up the usual allowance. A second search
   only when the first found nothing on the employer's own site and a different name for its programme
   (vacation program, cadetship, early careers) may find it.
   About 6 fetches and at most 2 searches per employer.
3. Decide:
   - `confirmed`: a page on the employer's own site or recruiting system describes a graduate, intern, vacation,
     cadet or early-careers programme **in this country**, or lists such a role located in this country. A global
     firm's early-careers site counts when it lists a programme or role located in this country.
   - `no_intake`: the employer's site says it has no graduate or intern intake.
   - `careers_only`: you read its careers pages (and searched, when they showed nothing) and found no programme
     for this country.
   - `unreachable`: neither its pages nor the search results on its own site could be opened.
   The page must be current: an intake, closing date or posting from 2025 or later, or a programme page the
   careers site links to now. A page about an intake of 2023 or earlier that nothing current links to is not
   `confirmed` (write `careers_only` and say so in `evidence`).
   Job boards (GradConnection, Prosple, Seek, Indeed, LinkedIn, Glassdoor, Handshake, WayUp, Vault, GradAustralia),
   recruitment agencies, news articles and university pages never count as `confirmed`: they only point to where to
   look on the employer's own site. A search result's summary is not the page: open the page.

## Output

One line per input employer, in input order, to `dist/checks/<cc>-rNN.out.jsonl` (same rNN), with the Write tool,
written every 10 employers (rewrite the whole file each time with all lines so far). The fields and the `notes`
wordings are exactly those of `CHECK_BRIEF.md` (read its "Write one line" part): `name`, `status`, `programme`,
`hires`, `notes`, `evidence`. `notes` says only what the opened page states about who may apply, and `evidence`
is that sentence copied from the page you opened (not from a search summary), at most 25 words.

## Rules

- Use only Read, Write, Grep, WebFetch and WebSearch (no PowerShell or Bash). Never touch any file except your own
  `.out.jsonl`.
- Every employer gets step 1, and step 2 when step 1 found nothing; never write `careers_only` from the first
  pass's word alone, and never when a search result shows a programme page you have not opened.
- When the search budget runs out (WebSearch keeps failing), stop, write the lines done so far, and say so in the
  report: the rest will be run again. Do not fill the rest with guesses.
- Report at the end in at most 5 lines: confirmed / no_intake / careers_only / unreachable, how many with notes,
  and how many employers needed a search.
