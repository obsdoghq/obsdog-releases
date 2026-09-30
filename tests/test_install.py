"""Offline installer contracts; fixtures never contact GitHub or execute a release."""
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest


INSTALLER = Path(os.environ.get("OBSDOG_TEST_INSTALLER", Path(__file__).resolve().parents[1] / "install.sh"))
VERSION = "v9.8.7"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="obsdog-installer-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.install = self.root / "install path [glob] ; literal"
        self.release = self.root / "release"
        self.release.mkdir()
        self.log = self.root / "downloads"
        # Deliberately isolated PATH exercises either Linux coreutils or macOS shasum.
        for command in ("awk", "mktemp", "tar", "gzip", "mkdir", "chmod", "cp", "mv", "rm"):
            os.symlink(shutil.which(command), self.bin / command)
        self.checksum("sha256sum" if shutil.which("sha256sum") else "shasum")
        self.stub("uname", '#!/bin/sh\n[ "$1" = -s ] && echo "$TEST_OS" || echo "$TEST_ARCH"\n')
        self.stub("curl", '''#!/bin/sh
set -eu
output= url=
while [ "$#" -gt 0 ]; do
  case "$1" in --output) output=$2; shift 2 ;; https://*) url=$1; shift ;; *) shift ;; esac
done
case "$url" in
  "https://github.com/obsdoghq/obsdog-releases/releases/download/v9.8.7/obsdog_v9.8.7_${TEST_PLATFORM}.tar.gz"|"https://github.com/obsdoghq/obsdog-releases/releases/download/v9.8.7/checksums.txt") ;;
  *) exit 65 ;;
esac
printf '%s\n' "$url" >> "$TEST_LOG"
cp "$TEST_RELEASE/${url##*/}" "$output"
''')
        self.archive = self.release / f"obsdog_{VERSION}_linux_amd64.tar.gz"
        self.make_archive()

    def stub(self, name, source):
        path = self.bin / name
        path.write_text(source)
        path.chmod(0o755)

    def checksum(self, name):
        for old in ("sha256sum", "shasum"):
            (self.bin / old).unlink(missing_ok=True)
        if name:
            command = shutil.which(name)
            if not command:
                self.skipTest(f"{name} unavailable on test host")
            os.symlink(command, self.bin / name)

    def make_archive(self, entries=None):
        if entries is None:
            entries = [("obsdog", b'#!/bin/sh\n[ "$1" = version ] && echo v9.8.7\n')]
        with tarfile.open(self.archive, "w:gz", format=tarfile.USTAR_FORMAT) as archive:
            for name, content in entries:
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = 0o755
                archive.addfile(info, io.BytesIO(content))
        self.manifest()

    def manifest(self):
        self.digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        (self.release / "checksums.txt").write_text(f"{self.digest}  {self.archive.name}\n")

    def run_installer(self, *args, system="Linux", arch="x86_64", platform="linux_amd64"):
        env = dict(os.environ, PATH=str(self.bin), HOME=str(self.root),
                   TEST_OS=system, TEST_ARCH=arch, TEST_PLATFORM=platform,
                   TEST_RELEASE=str(self.release), TEST_LOG=str(self.log))
        return subprocess.run(["/bin/sh", str(INSTALLER), "--version", VERSION,
                               "--install-dir", str(self.install), *args],
                              env=env, text=True, capture_output=True)

    def test_linux_sha256sum_install_and_atomic_replacement(self):
        self.checksum("sha256sum")
        for _ in range(2):
            result = self.run_installer()
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.install / "obsdog").is_file())
        self.assertIn("linux_amd64.tar.gz", self.log.read_text())

    def test_linux_dry_run_does_not_install(self):
        result = self.run_installer("--dry-run", arch="amd64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.install.exists())

    def test_macos_shasum_fallback_selects_existing_asset(self):
        self.checksum("shasum")
        self.archive = self.release / f"obsdog_{VERSION}_darwin_arm64.tar.gz"
        self.make_archive()
        result = self.run_installer(system="Darwin", arch="arm64", platform="darwin_arm64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("darwin_arm64.tar.gz", self.log.read_text())

    def test_unsupported_platforms_reject_before_download(self):
        for system, arch in [("Linux", "aarch64"), ("Darwin", "x86_64"), ("FreeBSD", "amd64")]:
            with self.subTest(system=system, arch=arch):
                result = self.run_installer(system=system, arch=arch)
                self.assertEqual(result.returncode, 69, result.stderr)
        self.assertFalse(self.log.exists())

    def test_no_checksum_tool_rejects_before_download(self):
        self.checksum(None)
        self.assertEqual(self.run_installer().returncode, 69)
        self.assertFalse(self.log.exists())

    def test_tampering_preserves_existing_binary(self):
        self.assertEqual(self.run_installer().returncode, 0)
        before = (self.install / "obsdog").read_bytes()
        with self.archive.open("ab") as stream:
            stream.write(b"tamper")
        self.assertEqual(self.run_installer().returncode, 65)
        self.assertEqual((self.install / "obsdog").read_bytes(), before)

    def test_duplicate_and_missing_checksum_entries_fail_closed(self):
        manifest = self.release / "checksums.txt"
        entry = manifest.read_text()
        for content in [entry + entry, "", f"{self.digest}  unrelated.tar.gz\n"]:
            manifest.write_text(content)
            self.assertEqual(self.run_installer().returncode, 65)
            self.assertFalse(self.install.exists())

    def test_extra_archive_entry_is_rejected(self):
        self.make_archive([("obsdog", b"fixture"), ("extra", b"unexpected")])
        self.assertEqual(self.run_installer().returncode, 65)
        self.assertFalse(self.install.exists())

    def test_symlink_archive_entry_is_rejected(self):
        with tarfile.open(self.archive, "w:gz") as archive:
            info = tarfile.TarInfo("obsdog")
            info.type = tarfile.SYMTYPE
            info.linkname = "/bin/sh"
            archive.addfile(info)
        self.manifest()
        self.assertEqual(self.run_installer().returncode, 65)

    def test_symlink_destination_is_rejected(self):
        self.install.mkdir()
        (self.install / "obsdog").symlink_to(self.root / "absent")
        self.assertEqual(self.run_installer().returncode, 73)
        self.assertTrue((self.install / "obsdog").is_symlink())


if __name__ == "__main__":
    unittest.main()
