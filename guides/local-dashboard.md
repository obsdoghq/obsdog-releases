# Offline dashboard

Run `obsdog dashboard serve`, then open `http://127.0.0.1:47777`.
No project init, account or sync is required. The default is the same Personal
library used by the CLI from every directory; `--space spc_…` selects an exact
local library. A fresh Personal is lazily created; a broken explicit selection
fails rather than switching libraries. Stop the foreground server with Ctrl-C.

`obsdog wiki serve` serves the same application, announcing its `/wiki` reading
entrypoint. Only one service is needed. If port 47777 is occupied, use an explicit
`--port PORT` or `--port 0`; no silent port hopping. Reuse requires a matching
Space ID, binary version and release channel. No daemon is installed.

## What the UI shows

- Overview: current document/block counts, authored links, actual recorded uses,
  activity, feedback sample sizes and source declarations.
- Knowledge: server-rendered Markdown, substring search, exact result opening,
  current block evidence, labels, comments, revisions and sources.
- Graph: current in-Space document references, plus current open evidence and
  explanation comments. Exact-ID links only; code examples, external links,
  unresolved titles, stale/closed comments and question proposals are not edges.
  Larger tiles mean more unique neighbors. Thicker lines mean more distinct
  source blocks. Neither is a truth/usefulness score or semantic distance.
- Activity: 7/30/90-day UTC records split by all/human/agent attribution. Search,
  exposure, use and usefulness are not one funnel. Daily exact values accompany
  the chart. Current inventory is not fabricated historical growth.
- Sources: revision-bound checks with source version, method, scope, evidence
  and actor. Private source locators are supported. Declarations ≠ verification;
  a narrow claim check is not a full applicability assessment.

Activity/evaluation filters do not filter current inventory or source coverage.
Source coverage includes all actors; document sourcing need not be repeated on
every block. Old-revision task judgments retain their attribution. Zero samples
are unknown, not zero quality. Read errors are unavailable, not empty libraries.
The graph is bounded to 200 nodes/500 edges, source scans to 10,000 blocks/2,000
comments/16 MiB; truncation is visible. Source details show at most 200 current,
stale or conflicting records. No edit/approve/undo UI is added.

`obsdog insights show --days 30 --actor agent --format json` reads the same
snapshot without serving a page, creating a report or migrating the database.
Its current graph, source evidence and event-window aggregates share a read
transaction. Schema `obsdog.insights/v1` is a bounded local projection, not a new
sync protocol. `/_obsdog/insights` is the corresponding same-origin GET endpoint.

## Privacy and failure behavior

The server binds IPv4 loopback only. It rejects non-loopback Host headers,
foreign Origin headers and cross-site subresource requests. There is no CORS,
LAN discovery, remote script/font/image, analytics or diagnostic initialization
for dashboard/wiki/insights commands. CSP blocks remote document embeds.
Explicit source links leave the app only when clicked, with no referrer.
Same-machine processes and browser extensions are not isolated by loopback;
this is not a multi-user or remotely exposed server. Do not reverse-proxy it.

Passive views create no search, exposure, use or feedback records. An explicit
search records retrieval; opening its hit records selection/exposure as before.
Ordinary document browsing is not falsely counted as search exposure. Visible
idle views refresh every 60 seconds, with a manual Refresh button. A failed
refresh keeps the last result clearly marked stale; it never displays fake data.
No data is persisted in browser local storage or a service worker.

The local interface is the default observation workflow, not an automatic HTML
report export. Existing report files are untouched; the legacy `report create`
capability remains only for an explicitly requested portable snapshot.

## Why not scan from the hosted app?

Hosted JavaScript reading a local library is a separate trust boundary, even
without sync. Browser local-network restrictions also vary. An optional future
bridge would need explicit pairing, scoped tokens, allowed origins, revocation
and browser permission handling; it is not shipped in this release.
See [Chrome local network access](https://developer.chrome.com/blog/local-network-access).

## Outcome-first overview

Top 1/3/10 utilization uses distinct completed search runs with an exact,
same-actor direct use inside rank K, over runs with any observed use. Repeated
uses vote once per run. Show used runs / all searches as observation coverage;
unobserved use is unknown, not failed. This is not independent task success.
The CLI currently returns one bounded list, not paginated results. Historical
rank is recorded but page number/size are not; never infer them retroactively.
When all results are limited to ten, Top 10 among used runs must be 100%, so it
is not by itself evidence of good retrieval. Use smaller K and coverage together.

Useful ratings count explicit usefulness judgments; direct block updates exclude
initial import and split/merge successor revisions. Restructuring counts distinct
split/merge/move operations, not created blocks. Neither activity proves quality
improvement. Missing outcome evidence is not fabricated from update counts.

Compare adjacent equal-duration trailing 7/30/90-day `[start,end)` UTC windows.
The daily chart has partial first/last days unless boundaries fall at midnight;
the detail panel displays exact intervals and values. Percentage-point changes
need samples on both sides. Older-period rates use evidence observed before
that period's end, not later uses. Inventory and current source state are separate
from time-windowed measurements. Actor filters do not filter inventory.
