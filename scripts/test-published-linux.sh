#!/usr/bin/env bash
set -euo pipefail

# Read-only acceptance of already published assets, never a release builder.
expected="${1:?Pass the current published stable release}"
[[ "$expected" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 65
[[ "$(uname -s)/$(uname -m)" == Linux/x86_64 ]] || exit 69
unset OBSDOG_GITHUB_TOKEN GH_TOKEN GITHUB_TOKEN
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary="$(mktemp -d)"
trap 'rm -rf "$temporary"' EXIT
export OBSDOG_HOME="$temporary/profile"
release_url="https://github.com/obsdoghq/obsdog-releases/releases/download/$expected"

for file in install.sh checksums.txt; do
  curl --fail --silent --show-error --location --proto '=https' \
    --connect-timeout 10 --max-time 90 "$release_url/$file" -o "$temporary/$file"
done
# Only the installer has been downloaded; verify its exact manifest entry.
entry="$(awk '$2 == "install.sh" {print}' "$temporary/checksums.txt")"
[[ "$entry" =~ ^[0-9a-f]{64}[[:space:]]+install\.sh$ ]] || exit 65
(cd "$temporary" && printf '%s\n' "$entry" | sha256sum --check --status -)

destination="$temporary/fresh install [glob] ; literal"
installer_tmp="$temporary/temporary files [glob] ; literal"
mkdir "$installer_tmp"
TMPDIR="$installer_tmp" sh "$temporary/install.sh" --install-dir "$destination" --dry-run
[[ ! -e "$destination/obsdog" ]]
# No --version override: the published installer's default must match its tag.
TMPDIR="$installer_tmp" sh "$temporary/install.sh" --install-dir "$destination"
cli="$destination/obsdog"
"$cli" version --format json | jq -e --arg expected "$expected" \
  '.ok == true and .data.version == $expected and .data.channel == "stable"' >/dev/null
"$cli" --licenses | grep -q 'Third-party notices'
"$cli" space default --ensure --format json | jq -e '.ok == true' >/dev/null
"$cli" space status --format json | jq -e '.ok == true and .data.local_only == true' >/dev/null
"$cli" document import --file "$root/tests/fixtures/linux-install.md" \
  --actor-type agent --actor release-linux-smoke --format json | jq -e '.ok == true' >/dev/null
"$cli" search --query comet --no-observe --format json | \
  jq -e '.ok == true and (.data.hits | length) == 1' >/dev/null
"$cli" trace list --format json | jq -e '.ok == true and (.data.rows | length) == 0 and .data.has_more == false' >/dev/null
"$cli" update --check --format json | jq -e --arg expected "$expected" \
  '.ok == true and .data.latest_version == $expected and .data.current_version == $expected and .data.owner == "standalone" and .data.update_available == false' >/dev/null
printf 'Published Linux %s: anonymous default install, local-only knowledge, unobserved probe and updater passed.\n' "$expected"
