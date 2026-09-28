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

Pages retain exact result identities/order/revisions through edits, restart and
backup. Replaying a page produces no extra search or returned-hit facts. A device
missing retained evidence fails explicitly rather than substituting live text.
Use the original device or start a new run. Old runs without page metadata can
still be opened but not paged. A changed query/filter needs a new search.

Use `--exclude-headings` to seek answer-body blocks. Reading a heading does not
mean reading its whole section. Scoped MCP clients use `obsdog_search_page`.

First-page use divides completed page-aware searches with explicit use of an
exact page-1 hit by all completed page-aware searches, including empty searches.
Legacy runs are excluded, not assigned an assumed page size. Top 1/3/10 among
used searches has a different denominator. Show observed use / all searches
alongside it; unrecorded use is unknown. Neither metric is first-query task
success or causal proof of better retrieval.

The default evaluator ID follows `--evaluator-type` in v0.2.3. When search used
a named agent, pass that same `--evaluator` only if it made the judgment. A
different evaluator remains an independent rating, not that searcher's own use.
