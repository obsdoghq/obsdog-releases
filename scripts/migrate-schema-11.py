#!/usr/bin/env python3
"""Optional offline v0.2.18 → v0.2.19 transition; check only unless --apply."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

GUIDE = "https://github.com/obsdoghq/obsdog-releases/blob/main/guides/local-schema-migration.md"
MAX_DATABASE = 8 * 1024**3


class MigrationError(Exception):
    pass


def command(cli: Path, *args: str) -> object:
    # Capture output locally: a failed CLI can include private Space information.
    try:
        result = subprocess.run(
            [str(cli), *args, "--format", "json"], capture_output=True,
            text=True, timeout=120, check=False,
            env={**os.environ, "OBSDOG_NO_UPDATE_NOTIFIER": "1"},
        )
        receipt = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise MigrationError("CLI stage unavailable; inspect it locally") from None
    if not isinstance(receipt, dict) or result.returncode or receipt.get("schema") != "obsdog.cli/v1" or receipt.get("ok") is not True:
        raise MigrationError("CLI stage refused; do not downgrade or retry blindly")
    return receipt.get("data")


def executable(value: str, version: str) -> Path:
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise MigrationError("Expected an executable from the reviewed release")
    if command(path, "version") != {"version": version, "channel": "stable"}:
        raise MigrationError(f"This helper requires stable {version}; use the guide for another version")
    return path


def selected_space(cli: Path, space: str) -> Path:
    catalog = command(cli, "space", "list")
    if not isinstance(catalog, list):
        raise MigrationError("Space catalog unavailable")
    selected = [entry for entry in catalog if isinstance(entry, dict) and entry.get("space_id") == space]
    if len(selected) != 1 or not isinstance(selected[0].get("path"), str):
        raise MigrationError("Select one exact existing local Space ID; no automatic default/enrollment")
    return Path(selected[0]["path"]).resolve(strict=True)


def quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def source_schema(root: Path) -> int:
    # Fail before using the legacy backup CLI against an already upgraded DB.
    # Require the reviewed mainline WAL-reset fix for this live read connection.
    if sqlite3.sqlite_version_info < (3, 51, 3):
        raise MigrationError("Apply needs Python linked to SQLite 3.51.3+; update Python or use a reviewed backport path")
    database = root / "obsdog.db"
    if database.is_symlink() or not database.is_file():
        raise MigrationError("Expected the selected Space's regular database")
    db = sqlite3.connect(database.as_uri() + "?mode=ro", timeout=3)
    try:
        db.execute("PRAGMA query_only=ON")
        db.execute("BEGIN")
        ledger = [row[0] for row in db.execute("SELECT version FROM schema_migrations ORDER BY version")]
        if ledger != list(range(1, 11)):
            raise MigrationError("Source is not schema 10; do not run the legacy writer or this migration again")
        if db.execute("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE name='feature_history_fence_v1')").fetchone()[0]:
            raise MigrationError("This is a fenced recovery source; preserve it without migration")
        return 10
    finally:
        db.close()


def archive_summary(archive: Path, expected_space: str, stage: Path) -> dict:
    # Only the immutable, consistent backup is opened with Python's SQLite.
    # Never use immutable=1 or a direct file copy against the live database.
    with zipfile.ZipFile(archive) as zipped:
        entries = zipped.infolist()
        if len(entries) != 2 or {entry.filename for entry in entries} != {"manifest.json", "obsdog.db"}:
            raise MigrationError("Unexpected backup archive shape")
        if any(entry.flag_bits & 1 for entry in entries):
            raise MigrationError("Encrypted/unreadable archive is not this transition format")
        if zipped.getinfo("manifest.json").file_size > 64 * 1024:
            raise MigrationError("Backup manifest exceeds the metadata bound")
        manifest = json.loads(zipped.read("manifest.json"))
        if not isinstance(manifest, dict) or manifest.get("space_id", manifest.get("workspace_id")) != expected_space:
            raise MigrationError("Backup Space identity differs from the exact selection")
        if not 0 < zipped.getinfo("obsdog.db").file_size <= MAX_DATABASE:
            raise MigrationError("Backup database is empty or exceeds 8 GiB; use a separately reviewed path")
        database = stage / "obsdog.db"
        with zipped.open("obsdog.db") as source, database.open("xb") as destination:
            shutil.copyfileobj(source, destination, 1024 * 1024)
    database.chmod(0o600)
    db = sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1")
    try:
        db.execute("PRAGMA query_only=ON")
        if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise MigrationError("Backup database integrity check failed")
        ledger = [row[0] for row in db.execute("SELECT version FROM schema_migrations ORDER BY version")]
        if not ledger or ledger != list(range(1, ledger[-1] + 1)) or ledger[-1] not in (10, 11):
            raise MigrationError("Backup has an unsupported stable schema ledger")
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        if "feature_history_fence_v1" in tables:
            raise MigrationError("This is a fenced recovery source; preserve it without migration")
        fingerprints = {}
        for table in tables:
            if table == "schema_migrations" or table.startswith(("sqlite_", "chunks_fts")):
                continue
            columns = [row[1] for row in db.execute(f"PRAGMA table_info({quoted(table)})")]
            digest = hashlib.sha256()
            digest.update(json.dumps(columns, separators=(",", ":")).encode())
            count = 0
            order = ",".join(quoted(column) for column in columns)
            for row in db.execute(f"SELECT {order} FROM {quoted(table)} ORDER BY {order}"):
                # Explicit value types keep BLOB/text and int/float distinct.
                values = [(type(value).__name__, value.hex() if isinstance(value, bytes) else value) for value in row]
                digest.update(json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode() + b"\n")
                count += 1
            fingerprints[table] = {"rows": count, "sha256": digest.hexdigest()}
        return {"schema": ledger[-1], "space_id": expected_space, "tables": fingerprints}
    finally:
        db.close()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_receipt(bundle: Path, receipt: dict) -> None:
    # Only the newly owned private bundle; never print raw CLI outputs/content.
    temporary = bundle / "receipt.tmp"
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(receipt, output, indent=2)
        output.write("\n")
    temporary.chmod(0o600)
    temporary.replace(bundle / "receipt.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", required=True, help="Exact local ID from space list, not personal/path")
    parser.add_argument("--previous-cli", required=True, help="Checksum-verified v0.2.18 executable outside PATH")
    parser.add_argument("--cli", required=True, help="Checksum-verified stable v0.2.19 transition executable")
    parser.add_argument("--backup-dir", type=Path, help="New private directory; never an existing directory or inside the Space")
    parser.add_argument("--apply", action="store_true", help="Back up, migrate through the existing CLI, verify")
    parser.add_argument("--writers-paused", action="store_true", help="Acknowledge all same-Space writers are paused; not a process detector")
    args = parser.parse_args(argv)
    bundle = None
    receipt = {"schema": "obsdog.local-migration/v1", "outcome": "checking", "stage": "versions", "guide": GUIDE}
    try:
        if not re.fullmatch(r"spc_[0-9a-f]{32}", args.space):
            raise MigrationError("Use the exact canonical Space ID from space list")
        if args.apply and (not args.writers_paused or args.backup_dir is None):
            raise MigrationError("Apply requires --writers-paused and a new --backup-dir")
        previous = executable(args.previous_cli, "v0.2.18")
        current = executable(args.cli, "v0.2.19")
        receipt["stage"] = "catalog"
        root = selected_space(current, args.space)
        if selected_space(previous, args.space) != root:
            raise MigrationError("Both runtimes must select the same exact local Space")
        if not args.apply:
            print("Metadata check passed. No database opened, backup made, migration or network request performed.")
            print("This is not schema/backup verification or proof that writers are paused.")
            return 0
        output = args.backup_dir.expanduser().absolute()
        if output.exists() or output.is_symlink():
            raise MigrationError("Backup directory already exists; preserve it and select a new path")
        output = output.resolve()
        if output == root or root in output.parents:
            raise MigrationError("Backup directory must be outside the selected Space")
        if root.parent.name == "spaces":
            profile = root.parent.parent
            if output == profile or profile in output.parents:
                raise MigrationError("Backup directory must be outside the entire ObsDog profile/catalog")
        output.mkdir(mode=0o700)  # Parent must exist; no broad tree creation.
        bundle = output
        receipt.update({"space_id": args.space, "stage": "schema-check"})
        write_receipt(bundle, receipt)
        source_schema(root)
        receipt["stage"] = "before-backup"
        write_receipt(bundle, receipt)
        before_file = bundle / "before.zip"
        command(previous, "space", "backup", "--space", args.space, "--output", str(before_file))
        with tempfile.TemporaryDirectory(prefix=".verify-", dir=bundle) as temporary:
            before = archive_summary(before_file, args.space, Path(temporary))
        if before["schema"] != 10:
            raise MigrationError("Before archive is not schema 10; migration has not been invoked")
        receipt.update({"before": before, "before_sha256": file_digest(before_file), "stage": "migration"})
        write_receipt(bundle, receipt)
        command(current, "space", "status", "--space", args.space)
        receipt["stage"] = "after-backup"
        write_receipt(bundle, receipt)
        after_file = bundle / "after.zip"
        command(current, "space", "backup", "--space", args.space, "--output", str(after_file))
        with tempfile.TemporaryDirectory(prefix=".verify-", dir=bundle) as temporary:
            after = archive_summary(after_file, args.space, Path(temporary))
        receipt.update({"after": after, "after_sha256": file_digest(after_file), "stage": "preservation-check"})
        if after["schema"] != 11 or any(after["tables"].get(name) != fingerprint for name, fingerprint in before["tables"].items()):
            raise MigrationError("Post-check failed: retain both archives; do not overwrite live data or use the old writer")
        receipt.update({"outcome": "verified", "stage": "complete"})
        write_receipt(bundle, receipt)
        print("Schema 10 → 11 verified; original table rows preserved. Keep the private backup bundle.")
        print("Reconnect host-owned MCPs and restart your dashboard with the same flags. No sync/process action was performed.")
        return 0
    except (MigrationError, OSError, ValueError, sqlite3.Error, zipfile.BadZipFile, RuntimeError) as error:
        if bundle is not None:
            receipt["outcome"] = "failed"
            try:
                write_receipt(bundle, receipt)
            except OSError:
                pass
        message = str(error) if isinstance(error, MigrationError) else "Inspection unavailable; inspect retained local evidence"
        print(f"Migration stopped: {message}. Guide: {GUIDE}", file=sys.stderr)
        if bundle is not None:
            print("Keep the private bundle; migration may have committed. No automatic rollback or cleanup was attempted.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
