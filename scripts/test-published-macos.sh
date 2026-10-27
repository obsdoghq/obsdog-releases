#!/usr/bin/env bash
set -Eeuo pipefail
expected="${1:?Pass the published stable version}"
[[ "$expected" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 65
[[ "$(uname -s)/$(uname -m)" == Darwin/arm64 ]] || exit 69
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Keep explicit historical baselines available; default to the preceding patch.
IFS=. read -r major minor patch <<< "${expected#v}"
(( 10#$major == 0 && 10#$minor == 2 && 10#$patch >= 31 )) || exit 65
previous="${2:-v0.2.$((10#$patch - 1))}"
exec bash "$root/scripts/test-published-update.sh" "$expected" "$previous"
