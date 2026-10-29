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

This example requires CLI v0.2.38 and an already installed Python3.9 or newer. Use two fresh
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
import json, os, shlex, sqlite3, sys, time
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
    (root / "holder-ready.json").write_text(json.dumps({"pid": os.getpid()}))
    if len(sys.argv) == 3:
        release = Path(sys.argv[2]).resolve()
        assert release.parent == root
        deadline = time.monotonic() + 120
        while not release.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("Synthetic holder timed out; fixture failed")
            time.sleep(0.1)
    else:
        try:
            input("Press Enter here to release only this synthetic writer: ")
        except EOFError:
            raise SystemExit("Holder lost stdin; fixture failed, do not measure as idle")
finally:
    (root / "holder-ready.json").unlink(missing_ok=True)
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

## Noninteractive holder and fixture checks

CLI v0.2.39+ is required for the --require-ready exit check below.

Do not measure until the synthetic holder has acquired its lock. Keep the setup
above through creation of hold.py, then replace its last foreground command with:

```sh
export repro_root
python3 - <<'PYTHON'
import json, os, subprocess, sys, time
from pathlib import Path
root = Path(os.environ["repro_root"]).resolve()
assert Path(os.environ["OBSDOG_HOME"]).resolve() == root / "profile"
release = root / "release"
with (root / "holder.out").open("w") as log:
    holder = subprocess.Popen([sys.executable, str(root / "hold.py"), str(root),
                               str(release)], stdin=subprocess.DEVNULL,
                              stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 10
        while not (root / "holder-ready.json").exists():
            assert holder.poll() is None, "Holder exited; fixture failed"
            assert time.monotonic() < deadline, "No acquired signal; fixture failed"
            time.sleep(0.05)
        assert json.loads((root / "holder-ready.json").read_text())["pid"] == holder.pid
        assert holder.poll() is None, "Holder exited; fixture failed"
        probe = subprocess.run(["obsdog", "space", "write-readiness",
                                "--require-ready", "--format", "json"],
                               capture_output=True, text=True, timeout=5)
        result = json.loads(probe.stdout)
        assert probe.returncode == 3 and result["data"]["status"] == "busy", result
        assert result["data"]["ready"] is False and holder.poll() is None, result
        owner = result["data"].get("writer_owner", {})
        if owner.get("pid"):
            assert owner["pid"] == holder.pid, owner
        print(probe.stdout, end="", flush=True)
        # Run only the printed synthetic commands from holder.out here.
        # Repeat the live-child/busy check before each additional measurement.
    finally:
        release.touch()
        holder.wait(timeout=8)
assert holder.returncode == 0, (root / "holder.out").read_text()
subprocess.run(["obsdog", "space", "write-readiness", "--require-ready",
                "--format", "json"], check=True, timeout=5)
PYTHON
```

This single controller owns the synthetic subprocess, acquired signal and release. It ignores stdin only when the
explicit release sentinel is selected, rolls back in finally, and expires after
120s. Shell teardown may still stop its children: check acquired signal, child
status and busy result before every measurement. The expected exit3 is checked inside the controller and cannot skip its finally. The controller's finally creates the release file and waits for only this test
child even when an assertion fails.
A missing OS lock sample does not prove the fixture was established. Never kill
an unrelated writer or remove live database files.

The OS interfaces report lock owner and range, not acquisition time. Neither
process uptime nor repeated samples proves a continuously held transaction.
Therefore transaction_age_ms may remain null with
transaction_age_unavailable_reason=os_lock_inventory_has_no_acquisition_time.

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

## Reproduce a dashboard warning without taking the live default port

Keep your live listener running. In a new disposable profile, start a previously
verified older CLI dashboard serve on an unused ephemeral port (--port 0); use
only the URL printed by that owned synthetic listener. With CLI v0.2.39+:

```sh
obsdog dashboard status --space SYNTHETIC_SPACE_ID --port PRINTED_PORT   --check-notice --format json
```

This explicitly invokes the same warning predicate for one selected loopback
listener and prints the notice on stderr. It does not stop or restart it. The
listener must identify the same synthetic Space and stable channel and an older
version. Different Spaces, equal/newer versions or unverifiable health do not
produce a stale warning. Ordinary command automatic probes still inspect only
the default port 47777; this controlled check is not a claim that the live
automatic warning occurred. Changing OBSDOG_HOME alone does not isolate TCP ports.
End only the test listener in its original foreground/subprocess context.

See [storage and backup](storage-and-backup.md) for freelist interpretation,
table/index byte attribution and optional private draft preservation.
