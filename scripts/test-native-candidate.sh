#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "Native candidate verification failed at line %s\n" "$LINENO" >&2' ERR
[[ $# == 2 && "$1" == /* && "$2" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "usage: $0 /absolute/candidate/obsdog vMAJOR.MINOR.PATCH" >&2
  exit 64
}
cli="$1"
version="$2"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/obsdog-native-smoke.XXXXXX")"
viewer_pid=
cleanup() {
  if [[ -n "$viewer_pid" ]]; then
    kill "$viewer_pid" 2>/dev/null || true
    wait "$viewer_pid" 2>/dev/null || true
  fi
  rm -rf "$temporary"
}
trap cleanup EXIT
export OBSDOG_HOME="$temporary/profile"
export OBSDOG_NO_UPDATE_NOTIFIER=1
unset GH_TOKEN GITHUB_TOKEN OBSDOG_GITHUB_TOKEN DBUS_SESSION_BUS_ADDRESS
[[ "$("$cli" version)" == "$version" ]]
"$cli" version --format json | jq -e --arg version "$version" \
  '.ok and .data.version == $version and .data.channel == "stable"' >/dev/null
"$cli" --licenses | grep -q 'Third-party notices'
"$cli" space default --ensure --format json > "$temporary/space.json"
space_id="$(jq -er '.data.space_id' "$temporary/space.json")"
"$cli" space status --space "$space_id" --format json | \
  jq -e '.ok and .data.initialized and .data.local_only' >/dev/null
printf '# Synthetic native evidence\n\nComet knowledge stays local.\n' > "$temporary/note.md"
"$cli" document import --space "$space_id" --file "$temporary/note.md" \
  --actor-type agent --actor release-native-smoke --format json > "$temporary/import.json"
document_id="$(jq -er '.data.document.document_id' "$temporary/import.json")"
"$cli" document read --space "$space_id" --id "$document_id" --format json | \
  jq -e '.ok and (.data.markdown | contains("Comet knowledge stays local."))' >/dev/null
"$cli" search --space "$space_id" --query comet --actor-type agent \
  --actor release-native-smoke --format json > "$temporary/search.json"
jq -e '.ok and (.data.hits | length) == 1' "$temporary/search.json" >/dev/null
"$cli" search --space "$space_id" --query comet --no-observe \
  --actor-type agent --actor release-native-smoke --format json | \
  jq -e '.ok and (.data.hits | length) == 1' >/dev/null

# Exercise the actual stdio transport, without enrolling a host plugin or account.
python3 - "$cli" "$space_id" "$version" "$temporary" <<'PY'
import json
from pathlib import Path
import select
import subprocess
import sys
import time

cli, space, version, temporary = sys.argv[1:]
with (Path(temporary) / 'mcp.stderr').open('w') as stderr:
    process = subprocess.Popen([cli, 'mcp', '--space', space], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=stderr, text=True)
    try:
        def send(message):
            process.stdin.write(json.dumps(dict(jsonrpc='2.0', **message)) + '\n')
            process.stdin.flush()

        def request(identity, method, params):
            send(dict(id=identity, method=method, params=params))
            deadline = time.monotonic() + 15
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
                    raise RuntimeError('native MCP response timed out')
                line = process.stdout.readline()
                if not line:
                    raise RuntimeError('native MCP closed stdout before its response')
                reply = json.loads(line)  # Human prose on protocol stdout fails here.
                if reply.get('id') == identity:
                    if 'error' in reply:
                        raise RuntimeError('native MCP returned a protocol error')
                    return reply['result']

        initialized = request(1, 'initialize', dict(protocolVersion='2024-11-05',
                              capabilities={}, clientInfo=dict(name='release-native-smoke', version='1')))
        if initialized['serverInfo']['version'] != version:
            raise RuntimeError('native MCP initialized with the wrong runtime version')
        send(dict(method='notifications/initialized'))
        tools = request(2, 'tools/list', {})
        required = {'obsdog_version', 'obsdog_space_status', 'obsdog_search',
                    'obsdog_search_probe', 'obsdog_document_read'}
        if not required.issubset({tool['name'] for tool in tools['tools']}):
            raise RuntimeError('native MCP is missing stable knowledge tools')
        result = request(3, 'tools/call', dict(name='obsdog_version', arguments={}))
        if result.get('isError') or version not in json.dumps(result):
            raise RuntimeError('native MCP version tool failed')
        process.stdin.close()
        process.wait(timeout=15)
        if process.returncode:
            raise RuntimeError('native MCP failed when its owned stdin closed')
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        process.stdout.close()
        if not process.stdin.closed:
            process.stdin.close()
PY
"$cli" trace list --space "$space_id" --format json | \
  jq -e '.ok and (.data.rows | length) == 1' >/dev/null
# Qualify new structural behavior with the actual platform executable.
# Historical distributions retain their original native smoke contract.
IFS=. read -r major minor patch <<< "${version#v}"
if (( 10#$major > 0 || 10#$minor > 2 || (10#$minor == 2 && 10#$patch >= 32) )); then
  printf '# Synthetic sections\n\n## First\n\nCometstructuralalpha evidence.\n\n## Second\n\nBeta evidence.\n\n## Third\n\nGamma evidence.\n\n## Fourth\n\nDelta evidence.\n' > "$temporary/sections.md"
  "$cli" document import --space "$space_id" --file "$temporary/sections.md" \
    --actor-type agent --actor release-native-smoke --format json > "$temporary/sections-import.json"
  section_doc="$(jq -er '.data.document.document_id' "$temporary/sections-import.json")"
  "$cli" document read --space "$space_id" --id "$section_doc" --structure --format json > "$temporary/sections-before.json"
  section_base="$(jq -er '.data.document.current_revision_id' "$temporary/sections-before.json")"
  roots="$(jq -er '[.data.blocks[1].block_id,.data.blocks[5].block_id] | join(",")' "$temporary/sections-before.json")"
  anchor="$(jq -er '.data.blocks[7].block_id' "$temporary/sections-before.json")"
  "$cli" search --space "$space_id" --query cometstructuralalpha --no-observe --format json > "$temporary/section-search-before.json"
  if "$cli" block move --space "$space_id" --ids "$roots" --after "$anchor" \
      --reason 'Synthetic missing-base refusal' --actor-type human --actor native-smoke \
      --format json > "$temporary/missing-base.json"; then
    echo 'A human batch accepted an inferred base.' >&2; exit 1
  fi
  jq -e '.ok == false' "$temporary/missing-base.json" >/dev/null
  "$cli" block move --space "$space_id" --ids "$roots" --after "$anchor" \
    --base-document-revision "$section_base" --reason 'Synthetic disjoint section move' \
    --actor-type agent --actor release-native-smoke --format json > "$temporary/move.json"
  jq -e '.ok and .data.care.status == "applied" and (.data.change.moved_block_ids | length) == 4' "$temporary/move.json" >/dev/null
  "$cli" document read --space "$space_id" --id "$section_doc" --structure --format json > "$temporary/sections-after.json"
  python3 - "$temporary" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
before = json.loads((root / 'sections-before.json').read_text())['data']
after = json.loads((root / 'sections-after.json').read_text())['data']
blocks = before['blocks']
assert len(blocks) == len(after['blocks']) == 9
assert [b['block_id'] for b in after['blocks']] == [blocks[i]['block_id'] for i in (0,3,4,7,8,1,2,5,6)]
prior = {b['block_id']: b for b in blocks}
for block in after['blocks']:
    expected = dict(prior[block['block_id']])
    expected['ordinal'] = block['ordinal']
    assert expected == block
assert before['document']['current_revision_id'] != after['document']['current_revision_id']
PY
  "$cli" search --space "$space_id" --query cometstructuralalpha --no-observe --format json > "$temporary/section-search-after.json"
  for phase in before after; do
    jq -e '.ok and (.data.hits | length) == 1 and (.data.hits[0].block_id | type) == "string" and (.data.hits[0].block_revision_id | type) == "string"' "$temporary/section-search-$phase.json" >/dev/null
    jq -S '.data.hits[0] | {block_id,block_revision_id,score}' "$temporary/section-search-$phase.json" > "$temporary/section-hit-$phase.json"
  done
  cmp "$temporary/section-hit-before.json" "$temporary/section-hit-after.json"
  jq -e --slurpfile before "$temporary/section-search-before.json" '
    (.data.index_snapshot_id | type) == "string" and
    (.data.hits[0].chunk_id | type) == "string" and
    .data.index_snapshot_id != $before[0].data.index_snapshot_id and
    .data.hits[0].chunk_id != $before[0].data.hits[0].chunk_id
  ' "$temporary/section-search-after.json" >/dev/null
  section_head="$(jq -er '.data.document.current_revision_id' "$temporary/sections-after.json")"
  "$cli" block move --space "$space_id" --ids "$roots" --after "$anchor" \
    --base-document-revision "$section_head" --reason 'Synthetic no-op' \
    --actor-type agent --actor release-native-smoke --format json | jq -e '.ok and .data.no_op == true' >/dev/null
  "$cli" document read --space "$space_id" --id "$section_doc" --format json | \
    jq -e --arg head "$section_head" '.ok and .data.document.current_revision_id == $head' >/dev/null
  echo 'Native disjoint subtree batch, explicit base, unchanged identities/search and no-op smoke passed'
fi
"$cli" dashboard serve --space "$space_id" --port 0 \
  > "$temporary/viewer.stdout" 2> "$temporary/viewer.stderr" &
viewer_pid=$!
url=
for _ in {1..50}; do
  url="$(sed -n 's/^ObsDog local viewer is available at \(http:\/\/127\.0\.0\.1:[0-9]*\)$/\1/p' "$temporary/viewer.stdout")"
  [[ -n "$url" ]] && break
  kill -0 "$viewer_pid"
  sleep 0.1
done
[[ "$url" =~ ^http://127\.0\.0\.1:[0-9]+$ ]]
curl -fsS --max-time 10 "$url/_obsdog/health" | \
  jq -e --arg version "$version" --arg space "$space_id" \
  '.version == $version and .channel == "stable" and .space_id == $space and .restart_required == false' >/dev/null
for route in / '/activity?lang=ko' '/graph?lang=en'; do
  [[ "$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' "$url$route")" == 200 ]]
done
echo 'Native isolated local-only import/read/search/probe, stdio MCP and loopback viewer smoke passed'
