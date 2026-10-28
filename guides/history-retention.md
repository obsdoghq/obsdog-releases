# History retention and recovery

The policy selected for the Space determines what expires. Installing a new
CLI alone does not change that policy.

- The original policy retains a historical version when it is among the latest
  ten including current **or** within seven days since supersession.
- The bounded policy supported by v0.2.37 retains a historical version only
  when it is among the latest ten including current **and** within seven days.
  The current version remains available. Uncertain old clocks and unverifiable
  history retain their explicit protection rather than inventing missing facts.

For the bounded policy, raw read/write/search/evaluation details expire seven
days after their first trusted server acceptance. Expiry does not reset when a
record is retried or copied. Original identifiers, hashes, byte counts, first
acceptance times and outcomes remain as compact evidence. Small immutable UTC
daily aggregates retain coverage and original counts without keeping raw query
or explanation text. An expired exact detail is explicitly unavailable.

The connected server must support and explicitly enable the bounded policy.
Use v0.2.37 or later on replicas that receive it. The separate activity capability
requires a complete verified checkpoint before activity updates can be accepted.
A missing or unsupported recovery checkpoint stops the operation instead of
silently dropping expiry evidence.

Current links follow document/block IDs. Exact historical reads disclose expiry.
Normal editing still checks the expected current revision to prevent overwriting
another edit.

## Explicit local cleanup

```sh
obsdog history retention --space SPACE_ID --prepare --format json
obsdog history retention --space SPACE_ID --format json
obsdog history retention --space SPACE_ID --apply --request UNIQUE_ID --snapshot PREVIEW_DIGEST --batch 100 --format json
```

Prepare does not delete bodies. Preview is read-only. Apply handles at most 100
versions and 100 bodies under the writer lock, rechecking the snapshot digest.
Retry an uncertain result with identical flags. Get a new preview and request ID
for another batch. Reported logical bytes are not immediate database-file
shrinkage. Local Apply is limited to never-synchronized stores without imported
or maintenance history that needs a connected recovery checkpoint. Do not remove
that history to bypass the guard.

## Cold recovery and original partial history

Use v0.2.30 or later for cold recovery. Matching built-in label definitions may
have different local creation times or descriptions; those differences do not
change their semantic identity. Conflicting definitions still stop recovery.

Some early history contains original events/evaluations without stored search
run, result or index details. Recovery preserves these as partial records, with
the original reference IDs and explicit missing evidence. It does not invent a
query, result, index or observation. `sync pull` reports the partial-record count;
`trace show --run RUN_ID` explains the unavailable evidence.

## Offline edits

```sh
obsdog history retention --space SPACE_ID --drafts --format json
obsdog history retention --space SPACE_ID --draft DRAFT_ID --format json
```

A new checkpoint preserves unresolved local heads and original pending work as
private recovery drafts. It pauses automatic upload, without claiming server
acknowledgment. This version does not automatically rebase these edits. Export
and review the draft, retain the original profile, restore a fresh replica from
the current server, then reapply selected edits against its current revisions.

## Connected backup recovery

From an authenticated current connection, export new recovery evidence:

```sh
obsdog sync checkpoint --space SPACE_ID --output CURRENT_RETENTION.json
obsdog space restore --backup BACKUP.zip --retention-checkpoint CURRENT_RETENTION.json
```

The export either reports no active checkpoint or carries the current complete
checkpoint, including the activity evidence and aggregate coverage when enabled. The restore verifies identity, hashes and covered cursor, reapplies
the expiry ledger in private staging, and preserves pending edits as drafts.
Missing, corrupt, foreign or older-than-installed evidence refuses recovery.

The file contains private knowledge and is trusted input from your authenticated
export, not a signed portable authorization. Obtain it anew for each restore;
do not substitute an older file. Keep recovery files private and retain them only
for the recovery session. The backup itself follows its separate retention
schedule. Restore never fabricates a search, a use or an evaluation. A backup or later
update cannot resurrect details expired by the current verified policy.

A legacy base revision may refer to an unavailable ancestor. History preserves
that original ID and reports the boundary. Affected documents stay protected
until their complete history can be verified; recovery never invents a parent.
