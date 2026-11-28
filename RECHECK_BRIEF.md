# Brief for the second look at an employer's graduate pages (read all of it before starting)

The first pass (`CHECK_BRIEF.md`) found no graduate or intern programme for the employers in your batch,
`dist/checks/<cc>-rNN.in.jsonl`. Many of them do run one: the first pass read only the pages a script could
open, and large employers often keep their programme on an early-careers site, a recruiting system (Workday,
SuccessFactors, Greenhouse, Lever, PageUp, Oracle, Avature, Eightfold…) or a page the careers home does not link.
Your job is to find it when it exists, and to be sure when it does not.

Each input line has `name`, `website`, `campus_site`, `site_candidates`, and what the first pass wrote:
`first_pass` (`careers_only`, `unreachable` or `no_intake`) and `first_page` (the page it read, maybe `""`).

## For each employer, in this order

1. **WebSearch** `<name> graduate program <country>` (for the United States: `<name> internship program`, or
   `<name> early careers` for a firm whose programme is not called an internship). Read the result list.
2. Open (WebFetch) the best result that is **on the employer's own domain or its recruiting system's page for the
   employer** (e.g. `<employer>.wd3.myworkdayjobs.com`, `careers.<employer>.com`, `jobs.<employer>.com.au`,
   `<employer>.pageuppeople.com`). Follow at most two links from it (Graduates, Students, Internships, Eligibility,
   FAQ). Then, if still nothing, one more search (`<name> internship <country>` or `<name> vacation program`,
   `<name> cadetship`, `<name> early careers`, whichever fits), and open its best result on the employer's own site.
   At most 2 searches and 5 fetches per employer.
3. Decide:
   - `confirmed`: a page on the employer's own site or recruiting system describes a graduate, intern, vacation,
     cadet or early-careers programme **in this country**, or lists such a role located in this country. A global
     firm's early-careers site counts when it lists a programme or role located in this country.
   - `no_intake`: the employer's site says it has no graduate or intern intake.
   - `careers_only`: you read its careers pages and searched twice, and found no programme for this country.
   - `unreachable`: neither its pages nor the search results on its own site could be opened.
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
- Every employer gets the two steps above; never write `careers_only` from the first pass's word alone.
- When the search budget runs out (WebSearch keeps failing), stop, write the lines done so far, and say so in the
  report: the rest will be run again. Do not fill the rest with guesses.
- Report at the end in at most 5 lines: confirmed / no_intake / careers_only / unreachable, how many with notes,
  and whether every employer got both searches.
