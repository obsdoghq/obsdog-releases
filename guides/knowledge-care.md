# Source-aware knowledge care

Available in CLI v0.1.14; connected Spaces require server v0.1.26 and compatible
active clients before the first care write. Native apps remain on hold. Upgrade
does not classify existing documents, crawl sources, enable sync, or install plugins.

## Agent workflow

1. Search the exact Space, read the relevant Markdown and check the real source.
2. Choose the knowledge's proper home. Repository instructions and code contracts
   stay in their repository; ObsDog stores a discovery pointer or useful synthesis,
   not an unmaintained duplicate. A snapshot is explicitly versioned/historical.
3. Inspect `document read --structure` or `block show` only when exact IDs/revisions
   are needed. Inspect `care show` for previous records and current stream heads.
4. Make a narrowly scoped content change if needed, then read it back. A single
   block update preserves one Markdown block and its type/depth. Use explicit
   structural operations for splitting/merging; do not smuggle a second paragraph.
5. Record only the source check or dimensions actually assessed. Read back the
   record. Sync only Spaces separately authorized for cloud sharing.

```sh
obsdog care show --space personal --format json
obsdog search --source-role pointer --temporal current --format json "deployment"
obsdog care record --file care.json --actor-type agent --actor codex --format json
```

All normal Space selection options apply. No `init` is needed. `care show` is
read-only; `care record` appends metadata, not document text. MCP exposes only
`obsdog_care_show` and source/temporal search options, not write tools.

## Source JSON

Use real IDs from the read result; this is a template, not a ready-to-submit fact.

```json
{
  "schema": "obsdog.knowledge-care-record/v1",
  "request_id": "task-source-1",
  "kind": "source",
  "key": "upstream",
  "target_type": "document",
  "target_id": "doc_FROM_READ",
  "revision_id": "rev_FROM_READ",
  "supersedes": [],
  "reason": "Keep the canonical source discoverable without copying its policy.",
  "source": {
    "role": "pointer",
    "temporal": "current",
    "owner": "Upstream documentation",
    "locator": "https://example.org/docs#install",
    "applicability": "A discovery pointer; the current claim has not been checked.",
    "check_scope": "none",
    "outcome": "not_checked"
  }
}
```

Roles: native/pointer/derived/snapshot. Temporal intent: current/historical/working;
it is not a deletion policy. External sources need a credential-free HTTPS URL
without query parameters. Never put local private paths or secrets in metadata.
Checks distinguish reachability, claim, applicability and claim_and_applicability.
Checked records also need outcome, checked_at, method and evidence. A semantic
supported outcome requires the examined version/observation ID. A working URL,
import timestamp or AI confidence is not proof of correctness.

## Review JSON and causality

For kind `review`, omit `source` and supply:

```json
{
  "rubric": "knowledge-care/v1",
  "method": "agent",
  "dimensions": {
    "context": {
      "value": "needs_work",
      "reason": "The procedure omits its required tool version.",
      "evidence": "The exact target revision mentions a command but no version."
    }
  }
}
```

Dimensions: home, fidelity, applicability, context, connections. Values: pass,
needs_work, unknown, not_applicable. Each needs reason/evidence. Omission means
unassessed. Set method to the actual agent/human/deterministic method. This is
authoring assessment, not retrieved/opened/used/useful feedback.

Reuse an identical request_id/input for retries. To correct a logical association,
use a new request_id, the same key, exact current revision and every current stream
head's event ID in `supersedes`. Review streams also include actor and rubric.
Offline sibling records remain a conflict; they never silently choose newest.
Changed content makes old checks stale. Explicit block provenance overrides a
document default even when the block's check is stale or conflicted.

## Measurement, safety and portability

Search filters run before the hit limit and are recorded with the care snapshot
digest in retrieval traces. Unfiltered search keeps unknown provenance visible.
`care show`, the local Wiki and private HTML report expose the bounded read model.
The web dashboard/inspectors provide the same data without knowledge editing UI.

Coverage is a current snapshot with eligible, unknown, stale and conflicting
targets. Reviews use the last 30 days in `[start,end)` UTC, by actor/method/rubric.
The defect rate is needs_work/(pass+needs_work), null for no assessed sample;
unknown, N/A and unassessed counts remain separate. Activity is not improvement.

Events are append-only. Inputs are at most 16 KiB; portable provenance framing is
at most 20 KiB. Recorded and imported event classes each have a per-Space bound of
4096 events/8 MiB. Exceeding a bound fails explicitly, never truncates a metric.
Current-state export/import preserves old records as `imported_evidence`, bound
to their original revision/Space, not fresh verification of new imported revisions.
Full backup/adoption preserves exact history. Portable manifests are bounded at
8 MiB, so large libraries must use the full backup path rather than partial export.
After new care events exist, do not roll back connected clients/server below the
compatible version floor. Back up before rollout; no history rewrite is necessary.
