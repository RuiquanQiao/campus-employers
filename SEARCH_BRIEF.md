# Brief for an agent finding homepages by search (read all of it before starting)

You get one batch file, `dist/search/todo-NN.tsv`: one employer per line, `sector<TAB>name<TAB>full name<TAB>hq`. These
employers hire graduates in mainland China, and none has a known homepage yet. Find each one's official homepage, and
its campus careers page when the same search shows it.

1. **One WebSearch per employer**, e.g. `<full name, or name if none> 官网`. Read the results; don't WebFetch.
   The search engine is US-based: for many state-owned groups a Chinese query returns only filings and news. Then
   one more search, in English: `<English name> official website` (e.g. `Shandong Iron and Steel Group official
   website`). A domain that a company database in the results (MarketScreener, OpenSanctions, CB Insights, Craft,
   Dealroom, gem.wiki) lists **for this same company** counts as found; the script opens it and checks the page.
   At most two searches per employer. Low yield is never a reason to stop.
2. **Homepage:** the employer's own site (`https://www.cscec3b.com`). Never an encyclopedia (百度百科, 维基), a company
   registry (企查查, 天眼查, 爱企查, 启信宝), a job board (智联, 前程无忧, BOSS, 猎聘, 应届生, 牛客), a news site, WeChat or
   Weibo. A subsidiary with no site of its own: leave it empty rather than give the group's.
3. **Careers page** (optional): only if a result is plainly its campus/careers page on its own domain or on a
   recruiting system's address naming it (`xxx.zhiye.com`, `app.mokahr.com/...`, `xxx.hotjob.cn`, `xxx.jobs.feishu.cn`,
   `iguopin.com` company page). Otherwise empty.
4. Not sure it is the same employer (another company with a similar name)? Leave both empty. A script opens every
   homepage and keeps it only if the page names the employer, so a near miss is dropped, but a wrong company's site
   that happens to share a word is worse than nothing.
5. **Write as you go**: every 15 employers, write the whole of `dist/search/done-NN.tsv` (same NN as your batch) with
   the Write tool: one line per employer done so far, `sector<TAB>name<TAB>homepage<TAB>careers page` (name exactly as in
   the todo file; empty fields stay empty but keep their tabs). Include employers you found nothing for, with both
   fields empty, so they count as done.
6. If WebSearch fails or says the budget is used up twice in a row, write the file as it stands and stop.
7. Report in two lines: how many of the batch you searched, how many homepages and careers pages you found, and the
   line you stopped at if you stopped early.
