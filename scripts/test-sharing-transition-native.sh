#!/usr/bin/env bash
set -euo pipefail
[[ $# == 5 && "$1" == /* && "$2" == /* && "$3" == /* && "$5" == /* ]] || {
  echo 'usage: test-sharing-transition-native.sh /old/obsdog /candidate/obsdog /candidate/obsdog-share-migrate vVERSION /private/output-parent' >&2
  exit 64
}
old="$1"; cli="$2"; helper="$3"; version="$4"
scratch="$(mktemp -d "$5/native-sharing.XXXXXX")"
chmod 700 "$scratch"
export OBSDOG_HOME="$scratch/profile" OBSDOG_NO_UPDATE_NOTIFIER=1
unset GH_TOKEN GITHUB_TOKEN OBSDOG_GITHUB_TOKEN DBUS_SESSION_BUS_ADDRESS
[[ "$("$old" version)" == v0.2.32 ]]
[[ "$("$cli" version)" == "$version" ]]
"$helper" --version | grep -F "obsdog-share-migrate $version · exact schema 12 → 13"
"$old" space default --ensure --format json > "$scratch/space.json"
space="$(jq -er '.data.space_id' "$scratch/space.json")"
printf 'Comet first proof.\n\nComet second proof.\n\nComet third proof.\n' > "$scratch/input.md"
"$old" document import --space "$space" --file "$scratch/input.md" --actor-type agent --actor native-sharing --format json > "$scratch/import.json"
document="$(jq -er '.data.document.document_id' "$scratch/import.json")"
block="$(jq -er '.data.blocks[0].block_id' "$scratch/import.json")"
base="$(jq -er '.data.blocks[0].current_revision_id' "$scratch/import.json")"
"$old" search --space "$space" --query comet --limit 1 --actor-type agent --actor native-sharing --format json > "$scratch/frozen.json"
run="$(jq -er '.data.retrieval_run_id' "$scratch/frozen.json")"
"$cli" document read --space "$space" --id "$document" --format json > "$scratch/read12.json"
dir="$OBSDOG_HOME/spaces/$space"
python3 - "$dir/obsdog.db" <<'PY'
import sqlite3,sys
with sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True) as db:
    assert db.execute('select max(version) from schema_migrations').fetchone()[0] == 12
PY
"$helper" --space-directory "$dir" > "$scratch/preview.json"
jq -e '.from_schema==12 and .to_schema==13 and (.committed|not)' "$scratch/preview.json" >/dev/null
"$helper" --space-directory "$dir" --writers-paused --apply --backup-dir "$scratch/transition-bundle" > "$scratch/receipt.json"
jq -e '.from_schema==12 and .to_schema==13 and .committed and .original_rows_preserved' "$scratch/receipt.json" >/dev/null
python3 - "$dir/obsdog.db" "$scratch/unchanged-before.sha256" <<'PY'
import hashlib,pathlib,sqlite3,sys
p=pathlib.Path(sys.argv[1]);assert sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True).execute('select max(version) from schema_migrations').fetchone()[0] == 13
pathlib.Path(sys.argv[2]).write_text(hashlib.sha256(p.read_bytes()).hexdigest())
PY
if "$old" block update --space "$space" --id "$block" --base-revision "$base" --content 'Unsupported old writer must not commit.' --reason 'synthetic refusal' --actor-type agent --actor native-sharing --format json > "$scratch/refused-old-writer.json" 2> "$scratch/refused-old-writer.stderr"; then
  echo 'old writer unexpectedly accepted schema13' >&2; exit 1
fi
python3 - "$dir/obsdog.db" "$scratch/unchanged-before.sha256" <<'PY'
import hashlib,pathlib,sys
assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()==pathlib.Path(sys.argv[2]).read_text()
PY
"$cli" document read --space "$space" --id "$document" --format json > "$scratch/read13.json"
python3 - "$scratch/read12.json" "$scratch/read13.json" <<'PY'
import json,sys
before,after=[json.load(open(p))['data'] for p in sys.argv[1:]]
assert before==after
PY
"$cli" block update --space "$space" --id "$block" --base-revision "$base" --content 'Comet changed proof.' --reason 'synthetic shared publication' --actor-type agent --actor native-sharing --format json > "$scratch/updated13.json"
"$cli" search page --space "$space" --run "$run" --page 2 --actor-type agent --actor native-sharing --format json > "$scratch/page2.json"
jq -e '.ok and .data.hits[0].rank==2 and (.data.hits[0].chunk_id|startswith("chk_"))' "$scratch/page2.json" >/dev/null
"$cli" search --space "$space" --query comet --actor-type agent --actor native-sharing --format json > "$scratch/shared-search.json"
jq -e '.ok and (.data.hits|all(.chunk_id|contains("_st_")))' "$scratch/shared-search.json" >/dev/null
python3 - "$dir/obsdog.db" "$scratch/populated-roots.db" <<'PY'
import os,sqlite3,sys
with sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True) as src:
    assert src.execute('select count(*) from snapshot_roots').fetchone()[0]>0
    with sqlite3.connect(sys.argv[2]) as dst: src.backup(dst)
os.chmod(sys.argv[2],0o600)
PY
printf 'Native schema12→13 transition, old-writer refusal, retained documents/frozen page and shared publication passed: %s\n' "$scratch"
