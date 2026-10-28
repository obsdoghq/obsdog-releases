# Accepted work, contention and correction recovery

Use installed help and `obsdog doctor` to verify capabilities before these steps.
Existing sessions keep their loaded guidance and executable until reconnected.

## Decide what was accepted

A successful content read does not establish a committed search observation.
For example, `ok: true` with returned Markdown and the following fields means
only the read succeeded:

```json
{
  "acceptance": {"read": "returned", "mutation": "not_attempted", "observation": "not_recorded"},
  "observation": {"persistence": "not_recorded", "reason": "writer_admission_refused", "use_available": false},
  "event_ids": []
}
```

Do not use or evaluate that unopened hit. If observation is needed, retry only
`search open --run RUN --rank RANK` for the same Space and actor after writer
release. Inspect observation again before use/feedback. Exact diagnostic reads
remain available but do not establish the committed-open prerequisite. A use
prerequisite refusal names the run/rank; it does not invent a persisted earlier
open-failure reason when that attempt was not retained across CLI processes.
Do not repeat an already accepted block/document edit to repair observation.

For a failed edit, inspect `mutation_state.persistence` and `evidence`:
`committed` means read the result without repeating the mutation; `unknown`
requires inspecting the original request/history; `not_committed` permits fresh
read and reconciliation of only the failed target. Current revisions are
observations, not reservations or proof of rollback. An unavailable readback has
an explicit status/reason. A committed deferred/failed Care receipt does not mean
the target edit committed. Keep original keys for receipt-backed retries.

## Recover a pending correction

`document corrections list --space SPACE_ID --format json` lists bounded local
metadata. Add `--draft ID` to inspect the original private intent. Read notices use
a document-specific pending index, independent of lifetime completed drafts and
other documents. Its 200-entry bound and partial/unavailable status are explicit;
completed/resolved entries leave that live index while audit history remains.
Recovery uses:

```sh
obsdog document corrections recover --space SPACE_ID --draft ID \
  --actor-type agent --actor ORIGINAL_ACTOR --format json
```

Recovery retains the original actor and revision bases. It does not silently
rebase over another writer. Repeating an already committed recovery does not
write again. If a newer writer makes the old correction stale, manually reconcile
the fresh document, author a separate new intent if needed, then explicitly record
the local disposition:

```sh
obsdog document corrections resolve --space SPACE_ID --draft ID \
  --revision CURRENT_DOCUMENT_REV --reason 'Manually reconciled current answer' \
  --actor-type agent --actor ORIGINAL_ACTOR --format json
```

Resolution does not edit the document or claim independent verification. Pending
notices on document/block/exact reads describe this local installation and do not
synchronize to another device. Preserve the private `correction-drafts` directory
alongside the profile before moving it: database-only Space backups omit these
files. Capture import uses its existing separate `document drafts`/`recover`
commands and original draft ID; do not replace uncertain recovery with a new fork.

## Bounds and writer samples

Single-shot commands share a default 60s cancellation deadline across preparation,
reservation and execution. Prefix `obsdog --timeout 90s ...` to change it; put the
flag before the command. A failed mutation may use an additional maximum 500ms
read-only head check. MCP and viewer requests have independent request limits.
Cancellation is not a rollback guarantee, and reservation budgets are not the
whole command duration. Progress and stale-dashboard notices use stderr.

`timings.writer_admissions[].attempts[].writer_owner` describes that specific
attempt; `admission_attempt`, `observed_at`, basis and sample span identify its
sample. A positive PID must not be summarized as unknown. A previous positive
sample and a later unavailable probe are separate attempts. `transaction_age_ms:
null` means age is unknown; sample span is not continuous lock age.

For controlled reproduction, use only a new disposable local profile and its
newly created synthetic Space. Keep one separately owned connection in a known
write transaction, run `space write-readiness` and a short `--timeout` edit from
another process, then release only that test connection and repeat the failed
open/edit. Compare PID, attempt time, total elapsed time and acceptance fields.
Never apply this procedure to an active library, terminate another writer,
remove WAL files or force an unlock. Healthy idle samples do not qualify busy
owner attribution. Linux synthetic acceptance uses this held/released scenario;
this release does not claim native macOS execution qualification.

## Reproduce a busy sample in a disposable profile

This example requires CLI38 and an already installed Python3.9 or newer. Use two fresh
terminal tabs and close those tabs afterward. It creates only synthetic knowledge
under a new temporary profile; it never opens your normal library. In terminal A:

```sh
repro_root="$(mktemp -d)"
export OBSDOG_HOME="$repro_root/profile" OBSDOG_NO_UPDATE_NOTIFIER=1
printf '# Synthetic test\n\nquartzneedle original answer.\n' > "$repro_root/note.md"
obsdog document import --file "$repro_root/note.md" --actor-type agent \
  --actor contention-fixture --format json > "$repro_root/import.json"
obsdog search --query quartzneedle --actor-type agent --actor contention-fixture \
  --format json > "$repro_root/search.json"
obsdog space status --format json > "$repro_root/status.json"
cat > "$repro_root/hold.py" <<'PYTHON'
import json, os, shlex, sqlite3, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
profile = Path(os.environ["OBSDOG_HOME"]).resolve()
assert profile == root / "profile"
status = json.loads((root / "status.json").read_text())["data"]
assert status["local_only"]
db = (Path(status["path"]) / "obsdog.db").resolve()
assert db.is_relative_to(profile) and db.is_file()
created = json.loads((root / "import.json").read_text())["data"]
run = json.loads((root / "search.json").read_text())["data"]["retrieval_run_id"]
block = created["blocks"][1]
connection = sqlite3.connect(f"file:{db}?mode=rw", uri=True)
try:
    connection.execute("BEGIN IMMEDIATE")
    print("Synthetic writer PID:", os.getpid(), flush=True)
    print("In terminal B, run these printed commands:", flush=True)
    print("export OBSDOG_HOME=" + shlex.quote(str(profile)) +
          " OBSDOG_NO_UPDATE_NOTIFIER=1", flush=True)
    print("obsdog space write-readiness --format json", flush=True)
    print(shlex.join(["obsdog", "search", "open", "--run", run, "--rank", "1",
          "--actor-type", "agent", "--actor", "contention-fixture",
          "--format", "json"]), flush=True)
    print(shlex.join(["obsdog", "--timeout", "2s", "block", "update", "--id",
          block["block_id"], "--base-revision", block["current_revision_id"],
          "--content", "quartzneedle corrected answer.", "--reason", "Synthetic test",
          "--actor-type", "agent", "--actor", "contention-fixture",
          "--format", "json"]), flush=True)
    input("Press Enter here to release only this synthetic writer: ")
finally:
    connection.rollback()
    connection.close()
PYTHON
python3 "$repro_root/hold.py" "$repro_root"
```

While A holds the transaction, B should observe busy admission and the sampled
writer PID when the OS exposes it. Open can return the original content with
observation not_recorded/use_available=false. The bounded edit can be refused;
inspect its actual mutation/draft state, including a preparation timeout. Age
can remain null. Press Enter in A, then retry only the original failed open or
recover only the reported correction draft with its original actor. Do not rerun
accepted siblings or use a new fork. Compare fresh exact content and revisions.
No production process is stopped, no forced unlock occurs and no cloud mode changes.

## Inventory and running dashboard

Every document list row states `lifecycle_state`. The default excludes settled
redirect/retired documents; `--include-retired` is the audit view. Exact historical
read and redirect targets remain available. Doctor excludes settled members from
current duplicate suggestions. `stale_cache` means a cached version below the
installed/running version, not a latest-release claim. Failed live checks remain
unavailable.

Ordinary CLI commands may warn on stderr about an older same-Space dashboard at
the default loopback port. Inspect `dashboard status`; for supported owned control:

```sh
obsdog dashboard restart --space SPACE_ID --port PORT
```

The command gracefully stops only the exact listener authenticated by its private
control record, then serves this executable in the foreground. It refuses another
Space or an older listener without supported control. Stop that older viewer in
its original foreground terminal once, then run `dashboard serve`. Do not kill a
guessed PID or restart independently owned MCP hosts.
