# Search pages and honest use measurements

```sh
obsdog search --query 'sync conflict' --limit 10 --actor-type agent --actor my-agent --format json
obsdog search page --run RUN_ID --page 2 --actor-type agent --actor my-agent --format json
obsdog search open --run RUN_ID --rank 11 --actor-type agent --actor my-agent --format json
```

Use the same Space and initiating actor. `rank` is global; `page_rank` is the
position on that page. Opening, use and feedback always take the global rank.
At most 100 candidates are retained; this is not an exhaustive result count.
Only delivered pages are recorded as returned hits. Unopened results stay
unjudged. Record use only when it actually helps, not to complete a walkthrough.

For a read-only current diagnostic, add `--no-observe --count-total` to
`obsdog search`. This optionally counts all matching current blocks under the
same filters without recording a retrieval run. It can cost more than the
bounded search and is not a historical run metric or a larger frozen page.

Pages retain exact result identities/order/revisions through edits, restart and
backup. Replaying a page produces no extra search or returned-hit facts. A device
missing retained evidence fails explicitly rather than substituting live text.
Use the original device or start a new run. Old runs without page metadata can
still be opened but not paged. A changed query/filter needs a new search.

For a deliberate QA or post-repair check on CLI v0.2.12+, use
`obsdog search --no-observe --query '<original query>'`. It uses the current
matcher/ranking and filters but creates no run, returned-hit record or metric;
its first-page rows cannot be opened or marked used. Use normal search for
actual task retrieval. Quoted terms require contiguous characters after
whitespace removal; a quoted no-hit may show the bounded candidate count if
quotes are removed. That is a reformulation hint, not evidence of an answer.

Use `--exclude-headings` to seek answer-body blocks. Reading a heading does not
mean reading its whole section. Scoped MCP clients use `obsdog_search_page` for
normal retrieval and `obsdog_search_probe` for non-observing diagnostics.

First-page use divides completed page-aware searches with explicit use of an
exact page-1 hit by all completed page-aware searches, including empty searches.
Legacy runs are excluded, not assigned an assumed page size. Top 1/3/10 among
used searches has a different denominator. Show observed use / all searches
alongside it; unrecorded use is unknown. Neither metric is first-query task
success or causal proof of better retrieval.

The default evaluator ID follows `--evaluator-type` in v0.2.3. When search used
a named agent, pass that same `--evaluator` only if it made the judgment. A
different evaluator remains an independent rating, not that searcher's own use.
