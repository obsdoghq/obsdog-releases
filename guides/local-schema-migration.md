# Local schema migration

## Published path: exact stable 11 → 12

Use CLI v0.2.23 and the separately verified transition assets from its same
immutable release. Do not migrate a library with a candidate or mismatched tool.
Historical v0.2.21 uses schema 11; its installation does not perform this
transition. The historical v0.2.19 path below remains unchanged.

CLI v0.2.23 preserves v0.2.22's schema 12. An already-transitioned schema-12
library needs no repeat migration. It creates new libraries at schema 12 and refuses other unfenced
schemas **before writable initialization**. It prints the actual and supported
schema with this guide's link. Normal CLI commands no longer retain or run a
historical migration chain. Installing a binary is not consent to migrate data.
Explicitly fenced recovery sources remain read-only.

Schema 12 shares historical chunk payload with immutable revisions and interns
snapshot titles. Chunk IDs, historical title/content, snapshot membership,
frozen result pages, events and pending operations remain unchanged. Validated
dashboard facts are derived locally from retained events; no ranking-policy
change, sync enrollment, upload or background service is introduced.

This read-oriented beta format is not a promise of faster writes or smaller WAL
files. Allow free space for the live database, temporary WAL and both consistent
backup snapshots. Do not delete live WAL/SHM files or downgrade an upgraded
library to reclaim space. See the [release scope and limits](../releases/v0.2.22.md#cost-and-scope).

### Prepare

1. Use a compatible server archive reader (v0.1.36 or newer) before migrating a connected Space.
   Local schema and remote sync protocol are different versions.
2. Keep the verified v0.2.21 executable outside PATH for isolated pre-transition
   recovery. Do not keep two competing normal CLI installations.
3. Download the migration archive for **your platform** and `checksums.txt`
   from the **same immutable v0.2.23 release**:
   `obsdog-migrate_schema11_to12_v0.2.23_darwin_arm64.tar.gz` on Apple silicon
   macOS, or `obsdog-migrate_schema11_to12_v0.2.23_linux_amd64.tar.gz` on Linux
   x86_64. Each archive has a packaged-binary SPDX SBOM in the same manifest. Verify
   the archive's SHA-256 before extracting its one `obsdog-migrate` executable.
   `./obsdog-migrate --version` identifies the reviewed tool build. Do not install
   it permanently in PATH. No Python or extra database library is required.
4. Get the exact local ID with `obsdog space list --format json`; it does not
   open or migrate that library. Pass its canonical directory, not a project
   path. For the default profile this is `~/.obsdog/spaces/<exact-space-id>`.

Read-only check:

```sh
./obsdog-migrate --space-directory /absolute/path/to/.obsdog/spaces/spc_EXACT_ID
```

Check verifies the exact stable schema-11 ledger, identity, integrity and foreign
keys, and refuses recovery fences. It creates no backup or network request.
It does not prove that writers are paused or that every transformation check
will pass; apply also validates chunk/revision agreement and supported consumers.

### Apply and verify

Pause agents and automation using this **same library**, let outstanding work
finish, stop the owned foreground viewer and disconnect host-owned MCPs in their
clients. `--writers-paused` acknowledges that step; it is not a process scan or
an automatic kill. Another device's separate local database needs its own
transition, not a filesystem-wide process shutdown.

Use a **new** private backup bundle outside the entire source profile. Its parent
must already exist. Existing output is refused, including on a retry:

```sh
./obsdog-migrate \
  --space-directory /absolute/path/to/.obsdog/spaces/spc_EXACT_ID \
  --backup-dir /absolute/path/outside-the-profile/schema12-backup \
  --apply --writers-paused
```

The helper takes consistent SQLite `before.db` and `after.db` snapshots, not a
live main-file copy that can omit WAL. Both and `receipt.json` and
`original-row-hashes.json` are private. It reserves a write transaction, checks
the source has not changed since backup, transforms the exact reviewed objects,
verifies every original logical table fingerprint and integrity/foreign keys,
then commits. Unsupported source content or custom chunk consumers cause refusal
and rollback, not silent normalization. Keep the whole bundle private.

After success, use the new CLI to read a known document and run `obsdog doctor`.
Use `search --no-observe` for a diagnostic query. Reconnect MCPs and check
`obsdog_version` inside their connections; restart the owned dashboard with its
previous flags and check `obsdog dashboard status`. Resume already-authorized
sync only after these checks. Do not manufacture use or feedback during testing.

### Compatibility and failure

- Current schema-12 writers pass a database compatibility fence. Legacy binaries
  without a future-schema guard cannot silently write the new physical format,
  but their errors may lack this modern guide link. Reconnect them; do not bypass
  the guard or remove ledger versions. This fence is not an authorization system.
- Fenced history is recovery evidence, not a new normal writable library.
- Keep partial backups and the receipt on failure. `committed: true` can coexist
  with a later backup or post-check failure. That is **not** a rollback.
- The helper never downloads or installs software, syncs, enables cloud storage,
  stops processes, overwrites outputs, or automatically downgrades.
- For pre-transition investigation, read `before.db` only with a read-only SQLite
  connection or a separately reviewed recovery profile. Do not place an old
  snapshot over live data or run a previous writer on an upgraded library. A
  downgrade would lose later writes and requires a separate recovery decision.

See [SQLite backup](https://www.sqlite.org/backup.html),
[VACUUM INTO](https://www.sqlite.org/lang_vacuum.html) and
[WAL](https://www.sqlite.org/wal.html). The tool embeds its reviewed SQLite runtime.

## Published path: stable 10 → 11

Installing CLI v0.2.19 is different from migrating a Space. The new runtime
migrates an unfenced schema-10 Space when it opens a writable Store. This includes
`space status`, `doctor`, document reads and searches; a command that sounds
read-only is not necessarily a passive database reader. `space list`,
`dashboard status` and passive dashboard views do not migrate it.

Schema 11 adds derived search-snapshot retention and run-eligibility structures.
It does not change document IDs, original revisions or ranking weights. It does
not sign in, enable sync, prepare structural Care or publish knowledge.

**Historical runtime behavior:** the immutable v0.2.19 binary still performs
its published automatic 10 → 11 migration. The v0.2.22
runtime instead refuses unsupported schemas and uses the version-specific
11 → 12 tool described above. That newer policy does not retroactively change
v0.2.19 or this historical helper. Use each helper only with its exact documented
source schema and runtime versions.

## Compatibility

| Runtime/data | Supported behavior |
| --- | --- |
| Stable v0.2.18, schema 10 | Continue normal local use during preparation |
| Stable v0.2.19, schema 10 | A writable open migrates to 11; passive views do not |
| Stable v0.2.19, schema 11 | Normal local use |
| Stable v0.2.18, schema 11 | Unsupported and unsafe, but this legacy binary has **no** future-schema refusal; disconnect it |
| Old idle MCP connected to this Space | It reopens per tool call and may still access upgraded data; it does not hold a writer forever, but must be disconnected |
| Another device with its own schema-10 database | Separate local migration; it is not this machine's shared-file writer |
| Fenced recovery source | Preserve its fence and schema; do not migrate it |

The cloud receiver must accept the archive/protocol used by each connecting
client. Local schema numbers are not sync protocol versions. Compatible server
archive readers accept exact schema-10 and schema-11 archives; they do not turn
an old same-file writer into a schema-11 writer.

Do not remove the ledger's version 11 to make the old CLI work. Old binaries do
not understand the new current-pointer and compaction semantics. Already
published binaries cannot acquire a new migration-link error message until they
are upgraded. A fresh shell's version also says nothing about an existing MCP.

## Prepare and check

1. Keep a checksum-verified v0.2.18 executable outside PATH before upgrading.
   Download it and `checksums.txt` from the same
   [immutable release](https://github.com/obsdoghq/obsdog-releases/releases/tag/v0.2.18).
   Use it only for this transition, not as a second permanent CLI.
2. Install stable v0.2.19. Do not yet run a Store-opening command on the target.
3. Read the [migration helper](../scripts/migrate-schema-11.py). Download it from
   a reviewed commit, then use Python 3.10+; no extra Python packages are needed.
   Apply additionally requires Python's SQLite 3.51.3+ for the reviewed WAL fix.
4. Obtain the exact local ID with `obsdog space list --format json`.
5. Run the metadata-only check. It makes no backup, migration or network request:

```sh
python3 migrate-schema-11.py \
  --space spc_FROM_SPACE_LIST \
  --previous-cli ./verified-v0.2.18/obsdog \
  --cli "$(command -v obsdog)"
```

This verifies executable versions and selection, **not** that all writers are
idle or that a backup has been tested. The helper intentionally supports only
v0.2.18 → v0.2.19. Use a separately reviewed path for older or future versions.

## Apply with a short writer pause

Stop new work against this Space and allow ongoing operations to finish. Pause
all agents/automation using its database. Stop the foreground dashboard and
disconnect host-owned MCPs through their clients; never kill unrelated processes.
v0.2.18 does not have a future-schema gate. Do not rely on its next call being
refused. Future clients must check compatibility, but that cannot retroactively
change this old process.

Use a **new** private backup directory outside the entire ObsDog profile. The
helper rejects existing outputs and directories inside its Space/catalog.
`--writers-paused` is your acknowledgement, not a
process scan or proof that writers stopped:

```sh
python3 migrate-schema-11.py \
  --space spc_FROM_SPACE_LIST \
  --previous-cli ./verified-v0.2.18/obsdog \
  --cli "$(command -v obsdog)" \
  --backup-dir ./obsdog-schema11-backup \
  --apply --writers-paused
```

The helper:

1. Takes a consistent `before.zip` using **v0.2.18**, checks schema 10, identity,
   archive shape, database integrity and absence of a recovery fence.
2. Runs v0.2.19 `space status` to invoke the existing transactional migration.
3. Takes `after.zip`, checks schema 11 and unchanged original table rows, and
   retains archive SHA-256 values and an outcome receipt.

Taking the before backup with v0.2.19 would migrate **before** the backup. A live
main-file copy can omit WAL state. The helper uses the CLI's supported consistent
snapshot instead. See [SQLite backup](https://www.sqlite.org/backup.html) and
[WAL documentation](https://www.sqlite.org/wal.html).

The helper never installs a binary, runs sync, edits SQL/ledgers, deletes archives,
restarts a process or automatically rolls back. It does not assert that a private
backup is safe to share. Keep the entire bundle private.

Before invoking the legacy backup runtime, apply mode reads the source schema
through a read-only SQLite connection and refuses an already upgraded or fenced
Space. It never uses `immutable=1` on the live database. Archive checks use that
mode only on an isolated, consistent extracted snapshot. Python linked to an
older SQLite is refused before this live read; update Python rather than bypass
the gate.

## Reconnect and verify

- Start a new/reconnected agent session and invoke `obsdog_version` in that
  connection. It must report v0.2.19; the old process can still report v0.2.18
even though it is no longer a supported client for the upgraded Space.
- Run `obsdog doctor --space spc_FROM_SPACE_LIST` and read one known document.
  Use `search --no-observe` only for a diagnostic query check.
- Restart your owned dashboard with the same Space/port flags. Check
  `obsdog dashboard status --port 47777 --format json`.
- Resume normal work. Sync only if that Space was already authorized/connected.

## Failure and recovery

On any failure, keep writers paused and inspect `receipt.json` and both archives
locally. The helper preserves partial evidence rather than printing CLI outputs
which might contain private data. A failed post-check does not imply the DB stayed
at schema 10: migration may have committed. Do not retry with the old writer.

Restore **before.zip with v0.2.18 into a new, separate recovery profile**, not over
the live Space. This inspects the previous state without discarding later writes:

```sh
recovery_profile="$(mktemp -d)"
OBSDOG_HOME="$recovery_profile" ./verified-v0.2.18/obsdog \
  space restore --backup ./obsdog-schema11-backup/before.zip --format json
```

The archive can retain existing sync/replica metadata. Do not run push/pull or
enroll it as another writer. Verify history/identity locally, then plan a
conditional recovery with the current runtime. Restoring an old snapshot is not
a lossless downgrade of work performed after migration.
