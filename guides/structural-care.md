# Restructure an explanation with exact history

CLI v0.2.35+ adds explicit structural Care. Existing schema12 libraries remain supported without automatic transition; fresh libraries use13. Check installed `care structure
--help` and `doctor` capabilities first. Local-only Spaces need no account. A
connected Space needs authenticated `document_structural_v1` preparation and
compatible active consumers. Update each long-running MCP/viewer separately.

Read `document read --id DOC --with-block-ids --format json` in the selected
Space. Keep exact document heads and use `--dry-run` before applying:

| Action | Intent |
| --- | --- |
| `retire-blocks` | Remove a complete section from the current view, retaining history without tombstone prose. |
| `insert-heading` | Add one heading before an existing paragraph or inside a section and recalculate parents. |
| `reparent-blocks` | Move complete roots inside one document, deliberately changing parent context. |
| `transfer-blocks` | Collect complete roots in another existing document in the same Space, retaining one-to-one successor lineage. Roots can be disjoint. |

```sh
obsdog care structure --action insert-heading --document DOC --base-revision REV --heading '# Title' --before FIRST_BLOCK --reason 'Add the intended document heading' --actor-type agent --actor AGENT --space SPACE --dry-run --format json
obsdog care structure --action transfer-blocks --document SOURCE --base-revision SOURCE_REV --ids ROOT_A,ROOT_B --target-document DEST --target-base-revision DEST_REV --after DEST_ANCHOR --reason 'Collect this topic with its explanation' --actor-type agent --actor AGENT --space SPACE --dry-run --format json
```

Replace placeholders with returned identities. Select each root once, in source
order; its descendants follow. An anchor stays outside selected roots. `--after`
means after the anchor's entire subtree. Remove `--dry-run` for the same reviewed
intent. Read both resulting documents and lineage after a transfer. An identical
intent with the original bases/options returns its original receipt. Changed
intent needs fresh reads. Compensation uses `care revert` and unchanged after
heads; it appends history and retains the new compatibility floor.

Check creates no documents, receipts, observations or compatibility floor. Applied
changes are atomic. Authored content/type/depth remains unchanged; a transfer
creates successors and retires source predecessors. Scoped links that cannot
retain meaning defer with known `offending_block_ids`. Inspect those blocks; do
not remove links, flatten paragraphs or rewrite code to force a change.

For manual plans, `care schema --format json` describes closed field types.
`care check` additionally checks exact heads, evidence, action applicability and
Markdown layout. Omit unused optional fields instead of null. Errors name field
paths without echoing private bodies. Prefer high-level commands for routine
changes. Ordinary update still requires one parsed block of the same type/depth.

## Diagnose contention and recover captures

`space status`, direct reads and `search --no-observe` use read-only paths in an
existing Space. They can still fail on other file, recovery or database errors.
One successful read is not proof that all reads always remain available.
`space write-readiness` separately performs a bounded reservation and rollback,
without repair, observation or content mutation. Its result is instantaneous and
does not reserve the next write. Unknown writer identity/transaction age remains
unknown. Stdio MCP provides `obsdog_write_readiness` separately from status.

Search, open, direct read and append have separate operation/timing diagnostics.
Search open/use/feedback record evidence and need writer admission. An admission
refusal includes operation/phase, attempts/backoff and elapsed/budget fields.
An honest unobserved search fallback has no recorded run/hit handle; do not count
it as observed or used. API unavailability and local Space contention are
different failures. Preserve the failing phase rather than assuming a lock.

Wait for the existing writer's outcome. Retry only a confirmed precommit
refusal; resolve uncertain outcomes through the original request. Preserve
failed `capture_…` drafts, then use `document drafts`/`document recover` with the
original actor and intent. A recovered original request retains document identity.
Do not kill another writer, edit the DB, restart services or change sync policy
as a generic recovery step. A single recovery does not establish root cause.

`doctor --guidance-version VERSION` compares caller-declared loaded guidance
with a bundled baseline. It does not inspect every installed plugin or reload a
long-running session. Check again after tool changes; an unknown version stays
unknown. Atomic multi-block update is not a universal speed guarantee.
