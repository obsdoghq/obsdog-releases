# Read availability and local maintenance

CLI v0.2.36 separates available knowledge from observation persistence. Inspect
`observation.persistence`, `retryable` and `retry_safe`: a known reservation
refusal can return `not_recorded` content without fabricated run/hit/event/use
records. Follow `next_read` with `block show --id BLOCK --revision REV` or an
advertised local MCP `obsdog_block_read`. Diagnostic reads do not establish an
observed use. Reopen an original recorded run after writer release before its
use workflow. An attempted commit with `unknown` persistence is not an automatic
retry: inspect the original trace/request first.

SQLite WAL allows readers with one physical writer per database, including
unrelated documents. Exact revision checks decide edit conflicts separately.
Ordinary open/publication does not run unrelated snapshot cleanup. Observation
reservations have a short independent cap; knowledge admission retains its
bounded allowance. Success/failure metadata exposes phases and admission attempts;
CLI progress stays on stderr and MCP protocol output stays machine-readable.
Writer diagnostics name an actually observed PID when supported, or explain
why ownership is unavailable. Same-PID sample span is not continuous lock age.
Do not kill another writer, remove DB/WAL files, change sync or rewrite SQLite
as a contention workaround.

## Retire a throwaway document

Read its exact head and preview `document retire --id DOC --base-revision REV
--reason TEXT --actor-type agent --actor ACTOR --space SPACE_ID --dry-run --format json`.
Apply the same authorized intent without `--dry-run`. Existing structural Care
preserves history and original-request replay without a sink document. Current
list/search omit retired documents. Use `document list --include-retired` and
exact read/history for audit or recovery. Update active consumers before structural
Care; see [the structural guide](structural-care.md).

## Reclaim physical space

`space compact --space SPACE_ID --format json` previews database/WAL bytes,
pages and free-page estimates without writes. Keep an accepted `space backup`
and choose an idle window before authorized `space compact --space SPACE_ID
--apply --format json`.

Apply runs one safe bounded unobserved-snapshot cleanup batch, SQLite's atomic
VACUUM and a bounded checkpoint attempt. Inspect actual before/after sizes and
checkpoint state: active readers/writers can defer checkpoint. Failure metadata
separates completed cleanup from physical reclamation. More explicit batches may
be needed for a backlog. Pinned runs, original facts, live history, schema/floors
and recovery drafts remain protected. VACUUM cannot reclaim live historical rows;
retirement preserves those rows. Compaction does not activate a new retention
policy or perform the separate schema12→13 transition.

## Find a failed capture

`document drafts --format json` includes effective title, original source_path,
draft ID and receipt state. A failed import exposes preserved-draft recovery
information. Recover the same draft/Space/original actor; it resolves an existing
receipt before writing, preventing duplicate import. A new import/fork is a new
intent. Ordinary append failure identifies the caller's unverified expected base
and does not promise a staged draft. Inspect status/read and the original Care
receipt before another intent.

Plugin installation does not upgrade the CLI or reload an existing MCP/viewer
or agent session. Check installed help/version and reconnect owned sessions at a
suitable milestone. These changes do not establish the cause of every historical
contention incident or a particular user's performance improvement.


## Repair parent metadata without rewriting content

Run `doctor --space SPACE_ID --format json` to inspect affected document counts,
structural block counts, legacy newline differences, scan completeness and
returned/remaining issues. Each item has the same block ID, zero-based ordinal,
40-character preview and blocking operations. A parent mismatch can block split
elsewhere in the document; permitted legacy terminal paragraph LF does not.

Read the document's exact head, then use:

```sh
obsdog document repair-parent-context --space SPACE_ID --id DOC_ID \
  --base-revision REV_ID --reason 'Repair stored parent context' \
  --actor-type agent --actor ACTOR --dry-run --format json
```

Review the proposed parent changes, then remove `--dry-run` to apply the same
intent. It preserves authored bytes, kind/depth, order, block IDs and content
revisions through existing structural Care. Other boundary mismatches are
refused. A clean exact head reports no_op without a receipt. An identical retry
finds the original receipt even after the head changed. Ordinary `block move`
preserves parents; explicit `care structure reparent` recalculates them.

`document update --dry-run` and `block move --dry-run` validate with no writer
reservation or receipt. Move preview needs `--base-document-revision REV_ID`.
Care `offending_block_ids` is available in35;36 adds response-only
`care_diagnostics` with all attributable IDs, ordinal, preview, counts and
completeness. Noncontiguous extraction names the whole conflicting range,
including gaps. Compare that span with the intended selection; do not silently
include gaps or strip headings/links to force a split.

Local MCP failures return `isError=true` and structuredContent with
`schema=obsdog.mcp-error/v1`, `error_code`, `message` and diagnostics; no normal
success `result` accompanies them. Treat failure separately from no knowledge.
Known prewrite observation fallback returns actual exact content with
`not_recorded` and `next_read`. Do not record use/evaluation for unopened results.

Total elapsed is wall time. Admission budget is the allowance at operation entry;
attempts show actual waits/backoff even on success. Prior admission spent is
already included in total elapsed. Phases can overlap and should not be summed.
An allowance is not an ETA. Each long-lived MCP request gets a fresh allowance.
Owner sampling reports an actual observed OS holder or an explicit unknown
reason; sample span is not proof of continuous transaction age.
