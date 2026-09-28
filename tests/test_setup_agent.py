import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "setup-agent.sh"


class SetupAgentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="obsdog-agent-setup-test-")
        self.addCleanup(self.temporary.cleanup)
        self.bin = Path(self.temporary.name) / "bin"
        self.bin.mkdir()
        self.log = Path(self.temporary.name) / "calls.log"
        self._stub("uname", '#!/bin/sh\n[ "$1" = "-s" ] && echo Darwin || echo arm64\n')
        self._stub(
            "brew",
            '#!/bin/sh\nprintf "brew %s\\n" "$*" >> "$SETUP_LOG"\n'
            'cp "$SETUP_BIN/obsdog_new" "$SETUP_BIN/obsdog"\n',
        )
        self._stub("obsdog_new", '#!/bin/sh\necho v0.2.4\n')
        self._stub(
            "codex",
            '#!/bin/sh\nprintf "codex %s\\n" "$*" >> "$SETUP_LOG"\n'
            'case "$*" in\n'
            '  "plugin marketplace list") echo "obsdog-skills /mock" ;;\n'
            '  "plugin list --json") echo \'{"installed":[{"pluginId": "obsdog@obsdog-skills"}]}\' ;;\n'
            '  "plugin add obsdog@obsdog-skills") [ "${FAIL_PLUGIN:-}" != yes ] ;;\n'
            'esac\n',
        )
        self._stub(
            "claude",
            '#!/bin/sh\nprintf "claude %s\\n" "$*" >> "$SETUP_LOG"\n'
            'case "$*" in\n'
            '  "plugin marketplace list") echo "obsdog-skills" ;;\n'
            '  "plugin list") echo "obsdog@obsdog-skills" ;;\n'
            'esac\n',
        )

    def _stub(self, name, source):
        file = self.bin / name
        file.write_text(source)
        file.chmod(0o755)

    def _run(self, *args, env=None):
        settings = os.environ.copy()
        settings.update(
            PATH=f"{self.bin}:/usr/bin:/bin",
            SETUP_BIN=str(self.bin),
            SETUP_LOG=str(self.log),
        )
        settings.update(env or {})
        return subprocess.run(
            ["/bin/sh", str(SCRIPT), *args],
            env=settings,
            text=True,
            capture_output=True,
            check=False,
        )

    def _calls(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_codex_existing_cli_refreshes_marketplace_without_brew(self):
        self._stub("obsdog", '#!/bin/sh\necho v0.2.5\n')
        result = self._run("--client", "codex")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("setup complete", result.stdout)
        self.assertIn("codex plugin marketplace upgrade obsdog-skills", self._calls())
        self.assertIn("codex plugin add obsdog@obsdog-skills", self._calls())
        self.assertNotIn("brew", self._calls())
        self.assertNotIn("sync", self._calls())

    def test_claude_fresh_cli_is_composed_in_one_run(self):
        result = self._run("--client", "claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("brew install obsdoghq/tap/obsdog", self._calls())
        self.assertIn("claude plugin install obsdog@obsdog-skills --scope user", self._calls())
        self.assertTrue((self.bin / "obsdog").exists())

    def test_existing_cli_does_not_require_homebrew(self):
        (self.bin / "brew").unlink()
        self._stub("obsdog", '#!/bin/sh\necho v0.2.4\n')
        result = self._run("--client", "claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("brew", self._calls())

    def test_missing_cli_without_homebrew_explains_recovery(self):
        (self.bin / "brew").unlink()
        result = self._run("--client", "codex")
        self.assertEqual(result.returncode, 69)
        self.assertIn("standalone CLI", result.stderr)
        self.assertEqual(self._calls(), "")

    def test_dry_run_changes_nothing(self):
        result = self._run("--client", "codex", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Would install", result.stdout)
        self.assertEqual(self._calls(), "")
        self.assertFalse((self.bin / "obsdog").exists())

    def test_outdated_cli_fails_before_plugin(self):
        self._stub("obsdog", '#!/bin/sh\necho v0.2.3\n')
        result = self._run("--client", "codex")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("older than v0.2.4", result.stderr)
        self.assertEqual(self._calls(), "")

    def test_plugin_failure_reports_partial_setup(self):
        self._stub("obsdog", '#!/bin/sh\necho v0.2.4\n')
        result = self._run("--client", "codex", env={"FAIL_PLUGIN": "yes"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CLI remains installed", result.stderr)

    def test_requires_explicit_client(self):
        result = self._run()
        self.assertEqual(result.returncode, 64)
        self.assertIn("choose --client", result.stderr)

    def test_rejects_unsupported_platform_before_install(self):
        self._stub("uname", '#!/bin/sh\necho Linux\n')
        result = self._run("--client", "codex")
        self.assertEqual(result.returncode, 69)
        self.assertEqual(self._calls(), "")


if __name__ == "__main__":
    unittest.main()
