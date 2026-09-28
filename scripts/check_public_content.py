#!/usr/bin/env python3
"""Redacted publication-content gate; supplements review, not a secret audit."""

from __future__ import annotations

import argparse
import html
import ipaddress
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

POLICY = "obsdog.public-content/v1"
MAX_BYTES = 4 * 1024 * 1024
BINARY_ASSETS = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2", ".ttf"}
PATTERNS = {
    "operator-home-path": r"(?:(?:file://|(?<![\w/]))/(?:Users|home|Volumes)/[^/\s\"<>]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)",
    "private-operations-repository": r"(?:github\.com/|git@github\.com:)?[a-z0-9_.-]+/(?:home[-_]hub|personal[-_]aws)(?![a-z0-9_-])",
    "internal-runbook-path": r"\b(?:hosts/(?:windows|macmini)/|runners/[a-z0-9_.-]+/)",
    "named-private-runner": r"\b[a-z0-9_]+-(?:ubuntu|linux|macmini|macos|windows)-(?:ci-)?obsdog[a-z0-9_-]*\b",
    "host-topology": r"\b(?:Mac\s+mini.{0,32}(?:deploy\w*|runner\w*|split[- ]DNS)|Windows\s+host.{0,48}Ubuntu\s+VM)\b",
    "real-knowledge-identifier": r"\b(?:spc|doc|blk|rev|rrn|evt|device)_[0-9a-f]{24,64}\b",
    "account-resource": r"\barn:aws[a-z-]*:[^:\s]+:[^:\s]*:\d{12}:",
    "private-key": r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----",
    "provider-credential": r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,})\b",
    "jwt-shaped-value": r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b",
}
RULES = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in PATTERNS.items()}
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
PRIVATE_NETS = tuple(ipaddress.ip_network(x) for x in (
    (0x0A000000, 8), (0xAC100000, 12), (0xC0A80000, 16), (0xA9FE0000, 16)
))
IPV6 = re.compile(r"(?<![\w:])(?:f[cd][0-9a-f]{2}|fe80)(?::[0-9a-f]{0,4}){2,7}(?![\w:])", re.I)


def findings(text: str) -> list[tuple[int, str]]:
    # Check ordinary text plus common HTML, JSON-slash and URL representations.
    normalized = html.unescape(unquote(text)).replace("\\/", "/").replace("\\\\", "\\")
    found: set[tuple[int, str]] = set()
    for line, value in enumerate(normalized.splitlines(), 1):
        for name, regex in RULES.items():
            if regex.search(value):
                found.add((line, name))
        for match in IPV4.finditer(value):
            try:
                address = ipaddress.ip_address(match.group())
            except ValueError:
                continue
            if any(address in network for network in PRIVATE_NETS):
                found.add((line, "private-network-address"))
        for match in IPV6.finditer(value):
            try:
                address = ipaddress.ip_address(match.group())
            except ValueError:
                continue
            if address.is_private or address.is_link_local:
                found.add((line, "private-network-address"))
    return sorted(found)


def selected_files(root: Path, paths: list[str], filesystem: bool, excludes: list[str]) -> list[Path]:
    if filesystem:
        candidates = [p for p in root.rglob("*") if ".git" not in p.relative_to(root).parts and (p.is_file() or p.is_symlink())]
    else:
        output = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        )
        candidates = [root / name for name in output.decode("utf-8").split("\0") if name]
    def within(name: str, prefix: str) -> bool:
        return name == prefix or name.startswith(prefix + "/")
    for name in [*paths, *excludes]:
        if not name or name in {".", "/"} or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Only explicit relative publication paths are accepted")
    for name in paths:
        if not (root / name).exists():
            raise ValueError("A requested publication path is missing")
    chosen = sorted(set(p for p in candidates if
        (not paths or any(within(p.relative_to(root).as_posix(), x) for x in paths))
        and not any(within(p.relative_to(root).as_posix(), x) for x in excludes)))
    if not chosen:
        raise ValueError("The publication surface is empty")
    return chosen


def audit(root: Path, paths: list[str], filesystem: bool, excludes: list[str]) -> tuple[list[tuple[str, int, str]], int, int]:
    problems: list[tuple[str, int, str]] = []
    count = binary = 0
    for path in selected_files(root, paths, filesystem, excludes):
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root and root in p.parents):
            problems.append((name, 0, "symlink-not-allowed"))
            continue
        if not path.is_file():
            problems.append((name, 0, "missing-tracked-file"))
            continue
        if path.suffix.lower() in BINARY_ASSETS:
            binary += 1
            continue
        if path.stat().st_size > MAX_BYTES:
            problems.append((name, 0, "text-size-limit"))
            continue
        try:
            with path.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                problems.append((name, 0, "text-size-limit"))
                continue
            text = raw.decode("utf-8")
            if "\0" in text:
                raise UnicodeError("Binary input")
        except UnicodeError:
            problems.append((name, 0, "unknown-binary-requires-review"))
            continue
        count += 1
        problems.extend((name, line, rule) for line, rule in findings(text))
    return problems, count, binary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--filesystem", action="store_true", help="Scan an export directory instead of Git files")
    parser.add_argument("--stdin", action="store_true", help="Scan bounded textual release metadata from stdin")
    parser.add_argument("--exclude", action="append", default=[], help="Explicit non-public relative subtree")
    parser.add_argument("paths", nargs="*", help="Explicit publication files/directories; default is the whole tree")
    args = parser.parse_args()
    if args.stdin:
        value = sys.stdin.read(MAX_BYTES + 1)
        if not value or len(value.encode("utf-8")) > MAX_BYTES:
            print("Publication metadata is empty or exceeds the bound.", file=sys.stderr)
            return 2
        problems = findings(value)
        for line, rule in problems:
            print(f"<stdin>:{line}: {rule} (matched value omitted)", file=sys.stderr)
        print(f"{POLICY}: release metadata; {len(problems)} findings")
        return 1 if problems else 0
    try:
        problems, count, binary = audit(args.root.resolve(), args.paths, args.filesystem, args.exclude)
    except (OSError, ValueError, subprocess.CalledProcessError):
        print("Publication scan unavailable; inspect the scoped input locally.", file=sys.stderr)
        return 2
    for path, line, rule in problems:
        print(f"{path}:{line}: {rule} (matched value omitted)", file=sys.stderr)
    print(f"{POLICY}: {count} text files; {binary} binary assets require separate review; {len(problems)} findings")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
