#!/bin/sh
set -eu

repository=obsdoghq/obsdog-releases
version=v0.2.20
install_dir=${OBSDOG_INSTALL_DIR:-"${HOME:?}/.local/bin"}
dry_run=false

usage() {
  cat <<'EOF'
Usage: install.sh [--version vMAJOR.MINOR.PATCH] [--install-dir DIRECTORY] [--dry-run]

Installs a checksum-verified ObsDog free beta for Apple silicon macOS or Linux x86_64.
No GitHub login is needed. The installer never changes Space data.
License and third-party notices are available with: obsdog --licenses
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      [ "$#" -ge 2 ] || { echo "--version requires a value" >&2; exit 64; }
      version=$2
      shift 2
      ;;
    --install-dir)
      [ "$#" -ge 2 ] || { echo "--install-dir requires a value" >&2; exit 64; }
      install_dir=$2
      shift 2
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

case "$(uname -s)/$(uname -m)" in
  Darwin/arm64) platform=darwin_arm64 ;;
  Linux/x86_64|Linux/amd64) platform=linux_amd64 ;;
  *) echo "release artifacts support Apple silicon macOS and Linux x86_64 only" >&2; exit 69 ;;
esac
case "$install_dir" in
  /*) ;;
  *) echo "--install-dir must be an absolute path" >&2; exit 64 ;;
esac
[ ! -L "$install_dir" ] || { echo "refusing a symlinked install directory" >&2; exit 73; }
[ ! -e "$install_dir" ] || [ -d "$install_dir" ] || { echo "install directory is not a directory" >&2; exit 73; }

for command in curl mktemp tar awk uname; do
  command -v "$command" >/dev/null 2>&1 || { echo "required command is missing: $command" >&2; exit 69; }
done

if command -v sha256sum >/dev/null 2>&1; then
  checksum_tool=sha256sum
elif command -v shasum >/dev/null 2>&1; then
  checksum_tool=shasum
else
  echo "required command is missing: sha256sum or shasum" >&2
  exit 69
fi
sha256() {
  if [ "$checksum_tool" = sha256sum ]; then sha256sum "$1"; else shasum -a 256 "$1"; fi
}

case "$version" in
  v[0-9]*.[0-9]*.[0-9]*) ;;
  *) echo "release version must be vMAJOR.MINOR.PATCH" >&2; exit 65 ;;
esac
printf '%s\n' "$version" | awk '/^v[0-9]+\.[0-9]+\.[0-9]+$/ { found=1 } END { exit found ? 0 : 1 }' || {
  echo "release version must be vMAJOR.MINOR.PATCH" >&2
  exit 65
}

temporary=$(mktemp -d "${TMPDIR:-/tmp}/obsdog-install.XXXXXX")
install_temporary=
cleanup() {
  [ -z "$install_temporary" ] || rm -f "$install_temporary"
  rm -rf "$temporary"
}
trap cleanup EXIT HUP INT TERM

archive_name="obsdog_${version}_${platform}.tar.gz"
for asset in "$archive_name" checksums.txt; do
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    --connect-timeout 10 --max-time 120 --max-filesize 67108864 \
    --output "$temporary/$asset" \
    "https://github.com/$repository/releases/download/$version/$asset"
done

archive="$temporary/$archive_name"
manifest="$temporary/checksums.txt"
[ -f "$archive" ] && [ ! -L "$archive" ] || { echo "release archive is missing or unsafe" >&2; exit 66; }
[ -f "$manifest" ] && [ ! -L "$manifest" ] || { echo "checksum manifest is missing or unsafe" >&2; exit 66; }

expected=$(awk -v name="$archive_name" '
  $2 == name || $2 == "*" name { print $1; matches += 1 }
  END { if (matches != 1) exit 1 }
' "$manifest") || { echo "checksum manifest must contain exactly one archive entry" >&2; exit 65; }
case "$expected" in
  *[!0-9A-Fa-f]*|'') echo "checksum manifest contains an invalid SHA-256 value" >&2; exit 65 ;;
esac
[ "${#expected}" -eq 64 ] || { echo "checksum manifest contains an invalid SHA-256 value" >&2; exit 65; }
actual=$(sha256 "$archive" | awk '{print $1}')
[ "$actual" = "$expected" ] || { echo "release archive checksum does not match checksums.txt" >&2; exit 65; }

entries=$(tar -tzf "$archive")
[ "$entries" = obsdog ] || { echo "release archive must contain exactly one top-level obsdog entry" >&2; exit 65; }
tar -tvzf "$archive" | awk 'NR==1 && substr($1,1,1)=="-" { regular=1 } END { exit (NR==1 && regular) ? 0 : 1 }' || {
  echo "release archive entry must be a regular file, not a link" >&2; exit 65;
}
mkdir "$temporary/extracted"
tar -xzf "$archive" -C "$temporary/extracted"
candidate="$temporary/extracted/obsdog"
[ -f "$candidate" ] && [ ! -L "$candidate" ] || { echo "release executable is missing or unsafe" >&2; exit 65; }
chmod 755 "$candidate"
[ "$("$candidate" version)" = "$version" ] || { echo "release executable version does not match the requested tag" >&2; exit 65; }

destination="$install_dir/obsdog"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  [ -f "$destination" ] && [ ! -L "$destination" ] || { echo "refusing to replace a non-regular or symlinked destination" >&2; exit 73; }
fi

if [ "$dry_run" = true ]; then
  echo "verified $version for installation at $destination"
  exit 0
fi

if [ ! -e "$install_dir" ]; then
  mkdir -p "$install_dir"
  chmod 755 "$install_dir"
fi
install_temporary=$(mktemp "$install_dir/.obsdog-install.XXXXXX")
cp "$candidate" "$install_temporary"
chmod 755 "$install_temporary"
[ "$("$install_temporary" version)" = "$version" ] || { echo "staged executable failed version verification" >&2; exit 74; }
mv -f "$install_temporary" "$destination"
install_temporary=
echo "installed $version at $destination"
