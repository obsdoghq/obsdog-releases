"""Offline transition orchestration; native acceptance uses only disposable homes."""

import contextlib
import importlib.util
import io
import json
import os
import select
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "migrate-schema-11.py"
SPEC = importlib.util.spec_from_file_location("schema_migration", SCRIPT)
MIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIG)
SPACE = "spc_" + "1a" * 16


def synthetic_archive(output, root, version=10, fenced=False, content="Original"):
    database = root / (output.stem + ".db")
    with contextlib.closing(sqlite3.connect(database)) as db, db:
        db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
        db.executemany("INSERT INTO schema_migrations VALUES(?)", [(i,) for i in range(1, version + 1)])
        db.execute("CREATE TABLE documents(id TEXT PRIMARY KEY, content TEXT, binary BLOB)")
        db.execute("INSERT INTO documents VALUES(?,?,?)", ("synthetic-note", content, b"\x01\x02"))
        if fenced:
            db.execute("CREATE TABLE feature_history_fence_v1(id INTEGER)")
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("manifest.json", json.dumps({"space_id": SPACE}))
        zipped.write(database, "obsdog.db")


class TransitionTests(unittest.TestCase):
    def exercise(self, arguments=(), *, fenced=False, after_content="Original"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            space = root / "space"
            space.mkdir()
            calls = []
            bundle = root / "bundle"

            def command(cli, *args):
                calls.append((cli.name, *args))
                if args == ("space", "list"):
                    return [{"space_id": SPACE, "path": str(space)}]
                if args[:2] == ("space", "backup"):
                    output = Path(args[-1])
                    synthetic_archive(output, root, 10 if cli.name == "old" else 11,
                                      fenced=fenced, content="Original" if cli.name == "old" else after_content)
                    return {"space_id": SPACE}
                if args[:2] == ("space", "status"):
                    return {"space_id": SPACE}
                raise AssertionError(f"Unexpected command {args[0]}")

            argv = ["--space", SPACE, "--previous-cli", "old", "--cli", "new"]
            if "--apply" in arguments:
                argv += ["--backup-dir", str(bundle)]
            argv += list(arguments)
            with mock.patch.object(MIG, "executable", side_effect=lambda value, version: Path(value)), \
                    mock.patch.object(MIG, "command", side_effect=command), \
                    mock.patch.object(MIG, "source_schema", return_value=10), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = MIG.main(argv)
            receipt = json.loads((bundle / "receipt.json").read_text()) if bundle.exists() else None
            retained = [name for name in ("before.zip", "after.zip") if (bundle / name).exists()]
            return code, calls, receipt, retained

    def test_default_is_catalog_only(self):
        code, calls, receipt, retained = self.exercise()
        self.assertEqual(code, 0)
        self.assertEqual([call[1:] for call in calls], [("space", "list"), ("space", "list")])
        self.assertIsNone(receipt)
        self.assertEqual(retained, [])

    def test_apply_requires_pause_before_any_cli_call(self):
        code, calls, receipt, retained = self.exercise(["--apply"])
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])

    def test_backup_precedes_migration_and_rows_are_verified(self):
        code, calls, receipt, retained = self.exercise(["--apply", "--writers-paused"])
        self.assertEqual(code, 0)
        self.assertEqual(receipt["outcome"], "verified")
        self.assertEqual([call[:3] for call in calls[2:]], [
            ("old", "space", "backup"), ("new", "space", "status"), ("new", "space", "backup"),
        ])
        self.assertEqual(retained, ["before.zip", "after.zip"])

    def test_fence_stops_before_migration(self):
        code, calls, receipt, retained = self.exercise(["--apply", "--writers-paused"], fenced=True)
        self.assertEqual(code, 1)
        self.assertNotIn(("new", "space", "status", "--space", SPACE), calls)
        self.assertEqual(receipt["outcome"], "failed")
        self.assertEqual(retained, ["before.zip"])

    def test_changed_rows_preserve_evidence_without_auto_rollback(self):
        code, calls, receipt, retained = self.exercise(["--apply", "--writers-paused"], after_content="Another writer")
        self.assertEqual(code, 1)
        self.assertEqual(receipt["stage"], "preservation-check")
        self.assertEqual(retained, ["before.zip", "after.zip"])
        self.assertFalse(any("restore" in call or "sync" in call for call in calls))

    def test_wrong_version_refuses(self):
        with mock.patch.object(MIG, "command", return_value={"version": "v9.9.9", "channel": "stable"}):
            with self.assertRaises(MIG.MigrationError):
                MIG.executable(sys.executable, "v0.2.18")

    def test_command_disables_network_notifier_and_redacts_failures(self):
        result = subprocess.CompletedProcess([], 1, '{"schema":"obsdog.cli/v1","ok":false,"error":"private-content"}', "private-log")
        with mock.patch.object(MIG.subprocess, "run", return_value=result) as run:
            with self.assertRaises(MIG.MigrationError) as error:
                MIG.command(Path("obsdog"), "version")
        self.assertEqual(run.call_args.kwargs["env"]["OBSDOG_NO_UPDATE_NOTIFIER"], "1")
        self.assertNotIn("private", str(error.exception))

    def test_duplicate_zip_entries_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "duplicate.zip"
            with zipfile.ZipFile(archive, "x") as zipped:
                zipped.writestr("manifest.json", "{}")
            with self.assertRaises(MIG.MigrationError):
                MIG.archive_summary(archive, SPACE, root)

    def test_source_schema_rejects_already_upgraded_before_legacy_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.closing(sqlite3.connect(root / "obsdog.db")) as db, db:
                db.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY)")
                db.executemany("INSERT INTO schema_migrations VALUES(?)", [(i,) for i in range(1, 12)])
            with mock.patch.object(MIG.sqlite3, "sqlite_version_info", (3, 53, 4)):
                with self.assertRaises(MIG.MigrationError):
                    MIG.source_schema(root)

    def test_no_overwrite_existing_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "existing"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("retain")
            with mock.patch.object(MIG, "executable", return_value=Path("fixture")), \
                    mock.patch.object(MIG, "selected_space", return_value=root / "space"), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = MIG.main(["--space", SPACE, "--previous-cli", "old", "--cli", "new",
                                 "--apply", "--writers-paused", "--backup-dir", str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(marker.read_text(), "retain")

    def test_backup_cannot_add_an_unexpected_catalog_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "profile"
            space = profile / "spaces" / SPACE
            space.mkdir(parents=True)
            bundle = profile / "spaces" / "backup"
            with mock.patch.object(MIG, "executable", return_value=Path("fixture")), \
                    mock.patch.object(MIG, "selected_space", return_value=space.resolve()), \
                    contextlib.redirect_stderr(io.StringIO()):
                code = MIG.main(["--space", SPACE, "--previous-cli", "old", "--cli", "new",
                                 "--apply", "--writers-paused", "--backup-dir", str(bundle)])
            self.assertEqual(code, 1)
            self.assertFalse(bundle.exists())


class MCP:
    def __init__(self, cli, env):
        self.process = subprocess.Popen([cli, "mcp"], env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.index = 0
        self.call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "migration-fixture", "version": "1"}})
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.process.stdin.flush()

    def call(self, method, params):
        self.index += 1
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.index, "method": method, "params": params}) + "\n")
        self.process.stdin.flush()
        while True:
            ready, _, _ = select.select([self.process.stdout], [], [], 15)
            if not ready:
                raise AssertionError("MCP fixture timed out")
            line = self.process.stdout.readline()
            if not line:
                raise AssertionError("MCP fixture exited")
            response = json.loads(line)
            if response.get("id") == self.index:
                return response

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.terminate()  # Exact owned disposable fixture process only.
            self.process.wait(timeout=3)
        self.process.stdout.close()


@unittest.skipUnless(os.environ.get("OBSDOG_SCHEMA10_TEST_CLI") and os.environ.get("OBSDOG_SCHEMA11_TEST_CLI"),
                     "Set both checksum-verified fixture CLI paths for native acceptance")
class NativeTransitionTests(unittest.TestCase):
    def test_actual_transition_legacy_mcp_boundary_and_recovery(self):
        old = os.environ["OBSDOG_SCHEMA10_TEST_CLI"]
        new = os.environ["OBSDOG_SCHEMA11_TEST_CLI"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {**os.environ, "OBSDOG_HOME": str(root / "profile"), "OBSDOG_NO_UPDATE_NOTIFIER": "1"}

            def run(cli, *args, expected=0):
                result = subprocess.run([cli, *args, "--format", "json"], env=env, text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, expected, "Native fixture stage failed")
                return json.loads(result.stdout)

            space = run(old, "space", "default", "--ensure")["data"]["space_id"]
            fixture = root / "note.md"
            fixture.write_text("# Original\n\nMigration beacon with preserved history.\n", encoding="utf-8")
            imported = run(old, "document", "import", "--file", str(fixture), "--space", space,
                           "--actor-type", "agent", "--actor", "fixture")["data"]
            document = imported["document"]["document_id"]
            original = run(old, "document", "read", "--id", document, "--space", space)["data"]["markdown"]
            # Keep an idle OLD connection through the migration, not an in-flight writer.
            mcp = MCP(old, env)
            try:
                self.assertFalse(mcp.call("tools/call", {"name": "obsdog_document_read", "arguments": {"document_id": document}})["result"].get("isError", False))
                bundle = root / "bundle"
                result = subprocess.run([sys.executable, str(SCRIPT), "--space", space, "--previous-cli", old,
                                         "--cli", new, "--backup-dir", str(bundle), "--apply", "--writers-paused"],
                                        env=env, capture_output=True, text=True, timeout=120)
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads((bundle / "receipt.json").read_text())
                self.assertEqual((receipt["before"]["schema"], receipt["after"]["schema"]), (10, 11))
                # Legacy v0.2.18 has no maximum-schema check. This regression
                # prevents the guide falsely promising retroactive refusal.
                legacy_read = mcp.call("tools/call", {"name": "obsdog_document_read", "arguments": {"document_id": document}})["result"]
                self.assertFalse(legacy_read.get("isError", False))
                version = mcp.call("tools/call", {"name": "obsdog_version", "arguments": {}})["result"]
                self.assertIn("v0.2.18", json.dumps(version))
                self.assertEqual(run(new, "document", "read", "--id", document, "--space", space)["data"]["markdown"], original)
                latest = MCP(new, env)
                try:
                    self.assertFalse(latest.call("tools/call", {"name": "obsdog_document_read", "arguments": {"document_id": document}})["result"].get("isError", False))
                finally:
                    latest.close()
                env["OBSDOG_HOME"] = str(root / "recovery")
                run(old, "space", "restore", "--backup", str(bundle / "before.zip"))
                self.assertEqual(run(old, "document", "read", "--id", document, "--space", space)["data"]["markdown"], original)
            finally:
                mcp.close()


if __name__ == "__main__":
    unittest.main()
