"""Synthetic publication-boundary regressions; never include real credentials."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_public_content.py"
SPEC = importlib.util.spec_from_file_location("public_content", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class PublicationTests(unittest.TestCase):
    def test_user_paths_public_endpoints_and_provenance_stay_allowed(self):
        self.assertEqual(CHECK.findings(
            "~/.obsdog $HOME/.local/bin http://127.0.0.1:47777 https://docs.obsdog.ai "
            "https://github.com/obsdoghq/obsdog-releases https://api.github.com/users/example/repos spc_FROM_READ doc_EXAMPLE "
            "sha256:" + "0" * 64
        ), [])

    def test_internal_paths_names_and_ids_are_detected(self):
        samples = [
            "/" + "Users" + "/example/Services/app",
            "/" + "Volumes" + "/example/app",
            "file://" + "/" + "Users" + "/example/Services/app",
            "C:" + "\\" + "Users" + "\\" + "example" + "\\" + "app",
            "https://github.com/example/" + "home" + "-hub/runbook",
            "`example/" + "home" + "-hub`",
            "hosts/" + "windows/runner/howto.md",
            "example-" + "ubuntu-ci-" + "obsdog-skills",
            "example-" + "linux-" + "obsdog-skills",
            "Windows " + "host's Ubuntu VM",
            "Mac " + "mini deployment",
            "spc_" + "a1" * 16,
            "arn:aws:s3::" + "1" * 12 + ":bucket",
        ]
        for sample in samples:
            with self.subTest(sample_type=samples.index(sample)):
                self.assertTrue(CHECK.findings(sample))

    def test_encoded_paths_are_detected(self):
        from urllib.parse import quote
        value = "/" + "Users" + "/example/Services/app"
        self.assertTrue(CHECK.findings(quote(value, safe="")))
        self.assertTrue(CHECK.findings(value.replace("/", "\\/")))
        self.assertTrue(CHECK.findings(value.replace("/", "&#47;")))

    def test_private_networks_not_documentation_or_loopback(self):
        for parts in [("10", "1", "2", "3"), ("172", "20", "1", "2"), ("192", "168", "1", "2"), ("169", "254", "1", "1")]:
            self.assertTrue(CHECK.findings(".".join(parts)))
        self.assertTrue(CHECK.findings("fd00" + "::1"))
        self.assertFalse(CHECK.findings("127.0.0.1 203.0.113.1 1.2.3.4 999.1.2.3"))

    def test_credentials_are_never_echoed(self):
        secret = "gh" + "p_" + "x" * 36
        self.assertTrue(CHECK.findings(secret))
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "README.md").write_text(secret)
            result = subprocess.run([sys.executable, str(SCRIPT), "--filesystem", "--root", tmp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(secret, result.stdout + result.stderr)
            self.assertIn("matched value omitted", result.stderr)

    def test_explicit_ops_exclusion_cannot_hide_shared_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ops").mkdir()
            (root / "_next").mkdir()
            forbidden = "example-" + "linux-" + "obsdog-web"
            (root / "ops" / "index.txt").write_text(forbidden)
            (root / "_next" / "shared.js").write_text(forbidden)
            problems, _, _ = CHECK.audit(root, [], True, ["ops"])
            self.assertEqual([p[0] for p in problems], ["_next/shared.js"])

    def test_empty_missing_and_broad_exclusions_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for paths, excludes in [([], []), (["missing"], []), ([], ["."]), (["../outside"], [])]:
                with self.assertRaises(ValueError):
                    CHECK.audit(root, paths, True, excludes)

    def test_unknown_binary_and_symlink_are_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "opaque.data").write_bytes(b"\xff")
            (root / "link.txt").symlink_to(root / "opaque.data")
            problems, _, _ = CHECK.audit(root, [], True, [])
            self.assertEqual({p[2] for p in problems}, {"unknown-binary-requires-review", "symlink-not-allowed"})


if __name__ == "__main__":
    unittest.main()
