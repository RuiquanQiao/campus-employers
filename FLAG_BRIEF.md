# Brief for marking which employers run a graduate programme (read all of it before starting)

You are given `dist/checks/<cc>-flag-NN.in.tsv`: employers whose graduate or intern programme was not found on
their own site by a script and a first look. Searching each of them again costs web searches, which are scarce, so
first you mark, **from what you know, with no web search and no fetch**, which of them run one.

For each line write one line to `dist/checks/<cc>-flag-NN.out.tsv` (same NN), with the Write tool, tab-separated:

    name<TAB>yes|no|unsure<TAB>what you know, in a few words

- `yes`: you know this employer runs a graduate, intern, summer/vacation, cadet or early-careers programme **in this
  country** (Australia: a graduate program, a summer vacation program, a cadetship; United States: a summer
  internship, a new-grad or rotational programme). A global firm counts only when its programme takes people in this
  country.
- `no`: you know it has none here (a one-office boutique, a fund with ten staff, a firm that hires only experienced
  people, an employer that has closed or merged into another).
- `unsure`: anything else. Don't guess `yes`.
- `name` exactly as in the input; keep the input's order and the header line `name\tmark\tknown`.
- When an employer has closed, merged or been bought, say so in the third column ("merged into Brighter Super").

Use only Read and Write. Write the file in parts as you go (rewrite the whole file each time). Report in 3 lines:
how many yes / no / unsure, and the closed or merged employers you noticed.
