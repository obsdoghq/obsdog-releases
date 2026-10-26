#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "Published macOS verification failed at line %s\n" "$LINENO" >&2' ERR
expected="${1:?Pass the published stable version}"
[[ "$expected" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 65
[[ "$(uname -s)/$(uname -m)" == Darwin/arm64 ]] || exit 69
unset GH_TOKEN GITHUB_TOKEN OBSDOG_GITHUB_TOKEN
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
export OBSDOG_HOME="$temporary/profile" OBSDOG_NO_UPDATE_NOTIFIER=1
fetch_installer() {
  local version="$1" destination="$2" entry
  mkdir "$destination"
  for asset in install.sh checksums.txt; do
    curl --fail --silent --show-error --location --proto '=https' --max-time 90 \
      "https://github.com/obsdoghq/obsdog-releases/releases/download/$version/$asset" \
      -o "$destination/$asset"
  done
  entry="$(awk '$2 == "install.sh" {print}' "$destination/checksums.txt")"
  [[ "$entry" =~ ^[0-9a-f]{64}[[:space:]]+install\.sh$ ]]
  (cd "$destination" && printf '%s\n' "$entry" | shasum -a 256 -c -)
}
fetch_installer "$expected" "$temporary/current"
sh "$temporary/current/install.sh" --install-dir "$temporary/fresh"
[[ "$("$temporary/fresh/obsdog" version)" == "$expected" ]]
fetch_installer v0.2.30 "$temporary/previous"
sh "$temporary/previous/install.sh" --install-dir "$temporary/retained"
cli="$temporary/retained/obsdog"
[[ "$("$cli" version)" == v0.2.30 ]]
printf 'Previous executable version verified.\n'
"$cli" space default --ensure --format json > "$temporary/space.json"
printf 'Previous local profile initialized.\n'
printf '# Synthetic retained evidence\n\nComet knowledge survives an update.\n' > "$temporary/note.md"
"$cli" document import --file "$temporary/note.md" --format json > "$temporary/import.json"
printf 'Retained fixture imported.\n'
document_id="$(jq -er '.data.document.document_id' "$temporary/import.json")"
"$cli" document read --id "$document_id" --format json > "$temporary/before.json"
jq -e '.ok and (.data.markdown | length) > 0 and (.data.document.current_revision_id | length) > 0' "$temporary/before.json" >/dev/null
printf 'Previous document body and revision verified.\n'
"$cli" update --check --format json > "$temporary/check.json"
jq '{ok,error_code:.error.code,version:.data.current_version,latest:.data.latest_version,available:.data.update_available,owner:.data.owner}' "$temporary/check.json"
jq -e --arg version "$expected" '.ok and .data.latest_version == $version and .data.update_available == true' "$temporary/check.json" >/dev/null
"$cli" update --format json > "$temporary/update.json"
jq -e '.ok and .data.updated == true and .data.previous_executable.copy_verified == true' "$temporary/update.json" >/dev/null
previous="$(jq -er '.data.previous_executable.relative_path' "$temporary/update.json")"
previous_hash="$(jq -er '.data.previous_executable.sha256' "$temporary/update.json")"
[[ "$previous" == .obsdog-recovery/* && "$previous" != *..* ]]
[[ "$(shasum -a 256 "$temporary/retained/$previous" | awk '{print $1}')" == "$previous_hash" ]]
[[ "$("$cli" version)" == "$expected" ]]
"$cli" document read --id "$document_id" --format json > "$temporary/after.json"
jq -S '.data | {markdown,revision_id:.document.current_revision_id}' "$temporary/before.json" > "$temporary/before-content.json"
jq -S '.data | {markdown,revision_id:.document.current_revision_id}' "$temporary/after.json" > "$temporary/after-content.json"
cmp "$temporary/before-content.json" "$temporary/after-content.json"
"$cli" search --query comet --no-observe --format json | \
  jq -e '.ok and (.data.hits | length) == 1' >/dev/null
"$cli" update --check --format json | jq -e --arg version "$expected" \
  '.ok and .data.current_version == $version and .data.latest_version == $version and .data.update_available == false' >/dev/null
printf 'Published macOS %s: anonymous default install and v0.2.30 retained-data update passed.\n' "$expected"
