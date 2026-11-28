# Brief for an agent guessing homepages (read all of it before starting)

Some employers in `data/cn/<sector>-NN.jsonl` have `"website": ""`. Your job: for **every** one of them in your
sector(s), give your best guesses at its official homepage. A script (`scripts/check_websites.py`) then opens each
guess and keeps the first whose page names the employer, so a wrong guess costs nothing and a right one is kept.
Guessing is the point here; leaving a name out is the only way to fail.

1. Don't use WebSearch or WebFetch. Work from what you know and from how such employers name their sites:
   - groups and subsidiaries: `www.<abbr>.com.cn`, `www.<abbr>.cn`, `www.<abbr>.com` (中建三局 → `https://www.cscec3b.com`,
     中铁四局 → `https://www.crfeb.com.cn`); a subsidiary often sits under its group's domain (`<x>.<group>.com.cn`);
   - 地方国企: pinyin initials of the city and line (`www.jxgt.com.cn`), or the full pinyin;
   - telecom provinces, banks' branches: the pattern the group uses;
   - listed firms: the domain in their English name or stock short name.
2. Give up to 3 guesses per employer, best first, and at least 1 for every employer: a pattern guess is fine.
3. Write `data/cn/<sector>.guesses.tsv` with the Write tool (or Python writing UTF-8, never a shell redirect): one line
   per employer, `<name exactly as in the file>\t<guess 1>\t<guess 2>\t<guess 3>`. Each guess is a full address starting
   with `https://` or `http://`. Don't edit the .jsonl files.
4. Only employers whose `website` is `""`; skip the others. Work file by file, appending as you go if the sector is
   large, so nothing is lost if you stop.
5. Report in two lines: how many employers had no homepage, how many you guessed for.

## Outside mainland China

The same task for `data/<cc>/<sector>-NN.jsonl` (you are given the country code): write
`data/<cc>/<sector>.guesses.tsv`. The page has to name the employer in a form its record has (`name`, `full_name` or an
alias), so a Japanese page naming 「静岡銀行」 holds for a record whose `full_name` or alias has it. Usual patterns:
- Japan: `www.<romanised name>.co.jp`, `www.<abbr>.co.jp`, `www.<name>.jp`; shinkin banks `www.<town>-shinkin.co.jp`;
  hospitals `www.<name>.or.jp`, `<name>.jcho.go.jp`; public bodies `www.<abbr>.go.jp`, prefectures `www.pref.<name>.lg.jp`;
  a group's subsidiary often under the group's domain (`www.<sub>.<group>.co.jp`) or `www.<group>-<sub>.co.jp`.
- Germany: `www.<name>.de`, `www.<name>.com`; Sparkassen `www.sparkasse-<town>.de`, Volksbanken `www.vb-<town>.de` or
  `www.voba-<town>.de`; universities `www.uni-<town>.de`.
- United Kingdom: `www.<name>.co.uk`, `www.<name>.com`; NHS trusts `www.<abbr>.nhs.uk`; councils `www.<name>.gov.uk`.
Then `scripts\check_websites.py --country <cc>` keeps the guesses that hold.
