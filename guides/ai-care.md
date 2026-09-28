# Bounded AI care

CLI v0.2.4 lets an authorized AI carry a small knowledge correction through
inspection, conditional change, readback and an attributable outcome. A human
can inspect the evidence and ask the AI for changes; there is no mandatory
per-item editing or approval queue.

## One supported change

Use `obsdog care --help` and the current plugin's `maintain` workflow. Read the
source and exact current document/block revisions. A private JSON plan declares
`schema: obsdog.care-plan/v1`, exact `space_id`, unique `request_id`, agent actor,
`action`, targets and base revisions, reason, checked evidence and complete
action-specific replacement. Use returned IDs, not titles or search ranks.

```sh
obsdog care check --space SPACE_ID --file plan.json --format json
obsdog care apply --space SPACE_ID --file plan.json --format json
obsdog care runs --space SPACE_ID --run RUN_ID --format json
```

The check is a preview, not a revision reservation. Apply checks every affected
head again. Read current Markdown and the receipt; an uncertain response calls
for request lookup before an identical retry. A changed plan needs a new request.
Actions are `update-block`, `split-block`, `merge-blocks`, `extract-document` and
`merge-documents`. Keep useful context and links; an unsupported shape defers.

Existing history and evaluations stay bound to their original identities and
revisions. Successors do not inherit a positive rating. Extracted/merged source
states remain traceable, including redirects and retired successors.

## An existing connected Space

Do not enroll a new connection merely to perform care. Check whole-Space upload
authority and that every active writer supports the new protocol. Server v0.1.29+
is required; exact-Space capability discovery is authenticated.

```sh
obsdog sync push --space SPACE_ID --format json
obsdog sync pull --space SPACE_ID --format json
obsdog sync prepare-care --space SPACE_ID --format json
```

Preparation refuses unresolved writes and binds capability to that Space/server.
It does not silently rewrite queued operations or select a different library.
After verified preparation, a care receipt and all affected content travel as
one operation. Check push/pull acknowledgement separately from local success;
remote conflicts remain explicit and require bounded reconciliation.

## Recovery and visibility

`applied` means the local transaction committed; `deferred` means no knowledge
change; `failed` means rollback with an outcome record when recording succeeded;
`reverted` means a new compensating transaction, not erased history.

An authorized `care revert` uses a new plan referencing the original run. It
refuses if any affected current head was changed by a later writer. Use an exact
Space backup for disaster recovery. History-unaware export/enrollment cannot
stand in for a complete care backup or synchronization history.

`obsdog insights show` and `obsdog dashboard serve` expose actual care outcomes.
These are activity counts with attribution and windows, not correctness scores
or proof that retrieval improved. No scheduler or source-deletion policy is added.
