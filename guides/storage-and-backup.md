# Storage and backup

Check installed help. CLI v0.2.39+ adds these explicit diagnostic fields/options.
Use only the selected authorized Space. Do not operate an active library merely
to reproduce a report.

## Understand physical space

space compact is a read-only preview unless --apply is passed. Its
reclaimable_free_page_bytes is exactly page_size * free_pages: a sampled freelist,
not a forecast of VACUUM savings or runtime. Zero freelist does not mean zero
unused bytes inside allocated pages. Database growth alone does not prove that
growth can be reclaimed.

The apply sequence is before sample, one bounded eligible unobserved-snapshot
cleanup, after_snapshot_cleanup sample, VACUUM, checkpoint and after sample.
Cleanup may free pages not counted by before. Concurrent sessions and checkpoint
timing can change database/WAL sizes between samples. Separate previews are not
reserved plans. Samples include sampled_at; duration_estimate_status=not_estimated
and vacuum_savings_estimate_status is explicitly unknown. Use actual timings to
plan later maintenance under similar conditions, without treating them as an ETA.

```sh
obsdog space compact --space SPACE_ID --storage-details --format json
```

This opt-in read-only dbstat scan has a default 2s budget (explicit --storage-details-budget 1ms..30s,
within the command deadline) and at most 1024 object rows.
Check storage_details.complete/status. If a large read-only scan expires,
explicitly select a longer allowance up to30s; it remains cancellable. Allocated, payload and unused page bytes
are shown per B-tree/table/index with categorized totals. This is metadata,
not document contents. The categories group object names and do not allocate
each byte to a user action. Freelist, WAL and file length are separate; partial/
unavailable is unknown rather than zero. Unused page bytes are not guaranteed
VACUUM savings.

Do not VACUUM repeatedly just because a DB is large. Inspect the object breakdown:
live history, frozen/pinned snapshots and retained observations cannot all be
freed by physical compaction. Where installed help supports it, history retention
without --apply previews its existing policy; applying/preparing retention is a
separate explicit operation with compatibility and recovery consequences.
This release does not silently shorten retention or delete authored history.
Keep an accepted backup and use an idle window for an authorized compact --apply.
It shares the default60s command deadline; choose an explicit prefix --timeout
for the accepted maintenance window. Cleanup can finish before a later VACUUM
refusal/cancellation, so inspect the reported phases and completion fields.

## Compare like-for-like backup bytes

space backup creates a ZIP/DEFLATE archive with manifest.json and an internally
consistent retained SQLite database from VACUUM INTO. All database-resident
tables, indexes, snapshots, events and retained history are copied. It is not a
current-document-only export. Archive bytes and compressed DB entry bytes can
be much smaller than database_uncompressed_bytes or the live file. This is not
evidence of lost history or a DB leak. A same-time internal DB/object comparison
is needed to explain a particular gap.

```sh
obsdog --timeout 5m space backup --space SPACE_ID --output NEW_BACKUP   --include-drafts --format json
```

The default backup omits private capture-drafts and correction-drafts. The explicit
--include-drafts option copies those two trees and a versioned SHA256/size inventory.
It detects changed file sets/content during copying and refuses symlinks/special
files. Stop all writers using that profile first: the DB and draft files are
not one atomic cross-file snapshot, and rechecks cannot prove absence of every
race. Limits: 10000 files, 64MiB per draft file and 512MiB combined. Failures remove
the new incomplete archive; an existing output is never overwritten.

Both modes omit profile identity, authentication material and dashboard runtime
controls. Database replica/history metadata is retained; restoration does not
authenticate or enroll a device. This is a Space data backup, not an authenticated
profile clone. Preserve it privately. Never publish draft contents or credentials.

## Restore privately without overwriting a library

Restore supports old DB-only archives and the new draft-bearing format; old CLIs
may reject draft-bearing archives. It validates paths, counts, sizes, hashes,
SQLite integrity and existing recovery constraints before publishing a fresh
Space. It refuses an already existing destination and does not erase a current
profile or select a new Personal Space.

```sh
# Use a NEW private recovery profile and an already accepted backup.
OBSDOG_HOME=NEW_RECOVERY_PROFILE obsdog --timeout 5m space restore   --backup BACKUP --format json
```

The default uncompressed DB entry limit remains 2GiB. For an intentionally larger
accepted backup, explicitly pass --max-database-bytes BYTES, up to 68719476736
(64GiB), and ensure adequate disk space. This option does not raise draft limits.
Restored drafts keep original IDs/actors/revision bases; inspect before recovery.
No sync, automatic draft replay, credential restoration or existing-file overwrite
is performed.
