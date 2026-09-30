#!/bin/sh
set -eu

# Compose the public CLI and the selected agent's public plugin.
# No ObsDog Space command runs during setup.
minimum_cli=v0.2.4
client=
dry_run=false

usage() {
  cat <<'EOF'
Usage: sh setup-agent.sh --client codex|claude [--dry-run]

Apple silicon macOS or Linux x86_64 Quick Start. Requires the selected agent CLI.
A missing CLI uses Homebrew on macOS or the standalone installer on Linux.
Installs or reuses ObsDog CLI, then installs the public ObsDog agent plugin.
Does not sign in, sync, seed knowledge, or edit AGENTS.md / CLAUDE.md.
Run `obsdog document list` after setup to inspect your local Personal Space.
EOF
}

fail() { printf 'ObsDog setup: %s\n' "$1" >&2; exit "${2:-1}"; }
has() { command -v "$1" >/dev/null 2>&1; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --client)
      [ "$#" -ge 2 ] || fail '--client requires codex or claude' 64
      client=$2
      shift 2
      ;;
    --dry-run) dry_run=true; shift ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; fail "unknown option: $1" 64 ;;
  esac
done

case "$client" in
  codex|claude) ;;
  *) usage >&2; fail 'choose --client codex or --client claude' 64 ;;
esac
case "$(uname -s)/$(uname -m)" in
  Darwin/arm64) platform=darwin_arm64 ;;
  Linux/x86_64|Linux/amd64) platform=linux_amd64 ;;
  *) fail 'this public CLI setup supports Apple silicon macOS and Linux x86_64 only' 69 ;;
esac
has "$client" || fail "$client is not on PATH; install the agent client first, then rerun this command" 69

version_at_least() {
  printf '%s\n' "$1" | awk -v minimum="$minimum_cli" '
    BEGIN { split(substr(minimum, 2), need, ".") }
    /^v[0-9]+\.[0-9]+\.[0-9]+$/ {
      split(substr($0, 2), got, ".")
      for (i = 1; i <= 3; i++) {
        if (got[i] + 0 > need[i] + 0) exit 0
        if (got[i] + 0 < need[i] + 0) exit 1
      }
      exit 0
    }
    { exit 1 }
  '
}

if has obsdog; then
  existing_version=$(obsdog version 2>/dev/null) ||
    fail 'existing obsdog command failed; repair it before installing the plugin' 70
  version_at_least "$existing_version" ||
    fail "existing obsdog $existing_version is older than $minimum_cli; update that installation and rerun" 70
  printf 'ObsDog CLI already available: %s\n' "$existing_version"
else
  if [ "$platform" = darwin_arm64 ]; then
    has brew || fail 'Homebrew is required to install a missing CLI; use the documented standalone CLI, then rerun setup' 69
    if [ "$dry_run" = true ]; then
      printf 'Would install ObsDog CLI %s or newer with Homebrew.\n' "$minimum_cli"
    else
      printf 'Installing ObsDog CLI through the official Homebrew tap...\n'
      brew install obsdoghq/tap/obsdog ||
        fail 'Homebrew CLI installation failed; fix the reported error and rerun' 70
    fi
  else
    has curl || fail 'curl is required for the standalone CLI installer' 69
    install_dir=${OBSDOG_INSTALL_DIR:-"${HOME:?}/.local/bin"}
    case "$install_dir" in
      /*) ;;
      *) fail 'OBSDOG_INSTALL_DIR must be an absolute path' 64 ;;
    esac
    if [ "$dry_run" = true ]; then
      printf 'Would install ObsDog CLI with the standalone installer at %s/obsdog.\n' "$install_dir"
    else
      temporary=$(mktemp -d "${TMPDIR:-/tmp}/obsdog-agent-setup.XXXXXX")
      trap 'rm -rf "$temporary"' EXIT HUP INT TERM
      curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
        --connect-timeout 10 --max-time 120 --max-filesize 1048576 \
        --output "$temporary/install.sh" \
        https://raw.githubusercontent.com/obsdoghq/obsdog-releases/main/install.sh ||
        fail 'standalone installer download failed; check your connection and rerun' 70
      sh "$temporary/install.sh" --install-dir "$install_dir" ||
        fail 'standalone CLI installation failed; fix the reported error and rerun' 70
      PATH="$install_dir:$PATH"
      export PATH
      printf 'Add %s to PATH in your shell profile for future agent sessions.\n' "$install_dir"
    fi
  fi
  if [ "$dry_run" != true ]; then
    has obsdog || fail 'installation finished but obsdog is not on PATH; fix PATH and rerun' 70
    installed_version=$(obsdog version 2>/dev/null) || fail 'installed CLI did not answer version' 70
    version_at_least "$installed_version" ||
      fail "installed CLI $installed_version is older than $minimum_cli; update the installation and rerun" 70
    printf 'ObsDog CLI ready: %s\n' "$installed_version"
  fi
fi

if [ "$dry_run" = true ]; then
  printf 'Would refresh obsdoghq/skills and install obsdog@obsdog-skills for %s.\n' "$client"
  printf 'No Space, account, project or global agent instructions would change.\n'
  exit 0
fi

printf 'Preparing the public ObsDog marketplace for %s...\n' "$client"
case "$client" in
  codex)
    if codex plugin marketplace list | grep -q '^obsdog-skills[[:space:]]'; then
      codex plugin marketplace upgrade obsdog-skills ||
        fail 'Codex marketplace refresh failed; rerun after checking your connection' 70
    else
      codex plugin marketplace add obsdoghq/skills ||
        fail 'Codex marketplace enrollment failed; rerun after checking your connection' 70
    fi
    codex plugin add obsdog@obsdog-skills ||
      fail 'Codex plugin installation failed; CLI remains installed, so rerun setup after fixing the plugin error' 70
    codex plugin list --json | grep -q '"pluginId": "obsdog@obsdog-skills"' ||
      fail 'Codex did not report the ObsDog plugin as installed; check codex plugin list --json' 70
    ;;
  claude)
    if claude plugin marketplace list | grep -q 'obsdog-skills'; then
      claude plugin marketplace update obsdog-skills ||
        fail 'Claude marketplace refresh failed; rerun after checking your connection' 70
    else
      claude plugin marketplace add obsdoghq/skills ||
        fail 'Claude marketplace enrollment failed; rerun after checking your connection' 70
    fi
    claude plugin install obsdog@obsdog-skills --scope user ||
      fail 'Claude plugin installation failed; CLI remains installed, so rerun setup after fixing the plugin error' 70
    claude plugin list | grep -q 'obsdog@obsdog-skills' ||
      fail 'Claude did not report the ObsDog plugin as installed; check claude plugin list' 70
    ;;
esac

printf '\nObsDog setup complete. CLI: %s; agent: %s plugin.\n' "$(obsdog version)" "$client"
printf 'Open a fresh %s session to use obsdog:find or obsdog:remember.\n' "$client"
printf 'First local check: obsdog document list\n'
printf 'Local dashboard: obsdog dashboard serve\n'
printf 'No knowledge was created or uploaded by setup.\n'

