"""Exercise structural Care and writer-independent reads on synthetic profiles."""
import json
import os
from pathlib import Path
import select
import sqlite3
import subprocess
import sys
import tempfile
import time

BIN, OLD = (Path(value).resolve() for value in sys.argv[1:3])
OUT = Path(tempfile.mkdtemp(prefix="native-structure-", dir=sys.argv[3]))
ENV = dict(os.environ, OBSDOG_HOME=str(OUT / "profile"), OBSDOG_NO_UPDATE_NOTIFIER="1")
RECORDS = []
ADOPTED = False


def run(*args, binary=BIN, ok=True):
    started = time.monotonic()
    result = subprocess.run([str(binary), *args], env=ENV, cwd=OUT,
                            capture_output=True, text=True, timeout=45)
    entry = dict(args=args, code=result.returncode, elapsed=time.monotonic()-started,
                 stdout=result.stdout, stderr=result.stderr)
    RECORDS.append(entry)
    (OUT / "commands.json").write_text(json.dumps(RECORDS, indent=2))
    assert (result.returncode == 0) == ok, entry
    body = json.loads(result.stdout)
    return body["data"] if ok else body


def counts(db):
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
        return connection.execute("SELECT (SELECT count(*) FROM documents),"
                                  "(SELECT count(*) FROM revisions),"
                                  "(SELECT count(*) FROM events),"
                                  "(SELECT count(*) FROM retrieval_runs)").fetchone()


def imported(name, markdown, binary=BIN):
    path = OUT / (name + ".md")
    path.write_text(markdown)
    return run("document", "import", "--file", str(path), "--format", "json", binary=binary)


def read(document):
    return run("document", "read", "--space", SPACE, "--id", document, "--with-block-ids", "--format", "json")


def structure(document, action, *extra):
    global ADOPTED
    args = ("care", "structure", "--action", action, "--document",
            document["document"]["document_id"], "--base-revision",
            document["document"]["current_revision_id"], "--reason",
            "Explicit synthetic structure acceptance", "--actor", "native-fixture", *extra,
            "--format", "json")
    frozen = counts(DB)
    assert run(*args, "--dry-run")["status"] == "ready"
    assert counts(DB) == frozen
    if not ADOPTED:
        imported("prior-after-dry-run", "# Prior writer remains allowed\n\nSynthetic independent note.\n", OLD)
    result = run(*args)
    ADOPTED = True
    assert result["status"] == "applied", result
    replay = run(*args)
    assert replay["replayed"] and replay["run_id"] == result["run_id"]
    return result


# Actual prior writer prepares this same schema13 profile before new adoption.
SPACE = run("space", "default", "--ensure", "--format", "json", binary=OLD)["space_id"]
DB = Path(ENV["OBSDOG_HOME"]) / "spaces" / SPACE / "obsdog.db"
document = imported("opening", "Opening paragraph.\n\nFirst fact.\n\nSecond fact.\n\n## Existing\n\nNested fact.\n", OLD)
DOC = document["document"]["document_id"]
observed = run("search", "--query", "Opening", "--actor-type", "agent", "--actor", "mcp-agent", "--format", "json")
assert run("care", "schema", "--format", "json")["additionalProperties"] is False
diagnostics = run("doctor", "--guidance-version", "0.3.32", "--require-capability", "document_structural_v1", "--require-capability",
    "write_readiness_v1", "--format", "json")
assert diagnostics["runtime"]["guidance_compatibility"] == "older_than_cli_baseline"

# The holder is a different process from every CLI and the stdio MCP server.
lock = sqlite3.connect(str(DB))
lock.execute("BEGIN IMMEDIATE")
try:
    frozen = counts(DB)
    run("space", "status", "--format", "json")
    run("search", "--no-observe", "--query", "Opening", "--format", "json")
    read(DOC)
    readiness = run("space", "write-readiness", "--format", "json")
    assert readiness["status"] == "busy" and not readiness["ready"]
    assert readiness["writer"] == "unknown" and readiness["transaction_age_ms"] is None
    process = subprocess.Popen([str(BIN), "mcp", "--space", SPACE], cwd=OUT, env=ENV,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
    sequence = 0

    def rpc(method, params):
        global sequence
        sequence += 1
        process.stdin.write(json.dumps(dict(jsonrpc="2.0", id=sequence,
                                           method=method, params=params)) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            assert select.select([process.stdout], [], [], max(0, deadline-time.monotonic()))[0], method
            line = process.stdout.readline()
            assert line, method
            reply = json.loads(line)
            if reply.get("id") == sequence:
                assert "error" not in reply, reply
                return reply["result"]
        raise AssertionError(method)

    try:
        rpc("initialize", dict(protocolVersion="2025-06-18", capabilities={},
                               clientInfo=dict(name="synthetic-native", version="1")))
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        process.stdin.flush()
        for name, arguments in [("obsdog_space_status", {}),
                                ("obsdog_search_probe", {"query": "Opening", "limit": 3}),
                                ("obsdog_document_read", {"document_id": DOC}),
                                ("obsdog_write_readiness", {})]:
            result = rpc("tools/call", dict(name=name, arguments=arguments))
            assert not result.get("isError"), result
        opened = rpc("tools/call", dict(name="obsdog_search_open", arguments={"retrieval_run_id": observed["retrieval_run_id"], "rank": 1}))
        (OUT / "mcp-open.json").write_text(json.dumps(opened, indent=2))
        assert opened["isError"], opened
        admission = opened["_meta"]["obsdog.ai/diagnostics"]
        assert admission["attempts"] and admission["writer"] == "unknown"
        assert opened["_meta"]["obsdog.ai/operation"] == "obsdog_search_open"
        result = rpc("tools/call", dict(name="obsdog_search", arguments={"query": "Opening", "limit": 3}))
        assert not result.get("isError"), result
        diagnostic = result["structuredContent"]["result"]
        assert diagnostic["observation_status"] == "not_recorded_writer_busy"
        assert diagnostic["diagnostic"] and not diagnostic.get("retrieval_run_id")
        assert diagnostic["observation_failure"]["attempts"]
        assert counts(DB) == frozen and lock.in_transaction
    finally:
        # Close only this test's stdio transport; never signal an existing writer.
        process.stdin.close()
        process.wait(timeout=10)
finally:
    lock.rollback()
    lock.close()
assert run("space", "write-readiness", "--format", "json")["rolled_back"]

heading = structure(document, "insert-heading", "--heading", "# Opening",
                    "--before", document["blocks"][0]["block_id"])
state = read(DOC)
assert state["blocks"][1]["parent_id"] == state["blocks"][0]["block_id"]
mid = structure(state, "insert-heading", "--heading", "## Split boundary",
                "--before", state["blocks"][3]["block_id"])
state = read(DOC)
assert state["blocks"][4]["parent_id"] == state["blocks"][3]["block_id"]
retired = structure(state, "retire-blocks", "--ids", state["blocks"][3]["block_id"])
assert len(retired["after"][0]["blocks"]) == len(state["blocks"]) - 2
assert "Split boundary" not in read(DOC)["markdown"]

moved = imported("parents", "# Root\n\n## Alpha\n\n### Child\n\nChild body.\n\n## Beta\n\nBeta body.\n")
reparented = structure(moved, "reparent-blocks", "--ids", moved["blocks"][2]["block_id"],
                      "--after", moved["blocks"][5]["block_id"])
child = next(block for block in reparented["after"][0]["blocks"]
             if block["block_id"] == moved["blocks"][2]["block_id"])
assert child["parent_id"] == moved["blocks"][4]["block_id"]
source = imported("interleaved", "# Mixed\n\n## One\n\nCase A.\n\nAgreement A.\n\n## Two\n\nCase B.\n\nAgreement B.\n")
target = imported("cases", "# Cases\n\nIntroduction.\n")
transferred = structure(source, "transfer-blocks", "--ids",
                        source["blocks"][2]["block_id"] + "," + source["blocks"][5]["block_id"],
                        "--target-document", target["document"]["document_id"],
                        "--target-base-revision", target["document"]["current_revision_id"],
                        "--after", target["blocks"][1]["block_id"])
assert len(transferred["lineage_edges"]) == 2
assert "Case A." not in read(source["document"]["document_id"])["markdown"]
assert "Case B." in read(target["document"]["document_id"])["markdown"]

# The actual previous executable must refuse a new write, also after recovery.
state = read(DOC)
def old_refusal():
    frozen = counts(DB)
    error = run("block", "update", "--space", SPACE, "--id", state["blocks"][1]["block_id"],
                "--base-revision", state["blocks"][1]["current_revision_id"],
                "--content", "Must not be written.", "--reason", "Synthetic prior writer refusal",
                "--actor-type", "agent", "--actor", "native-fixture", "--format", "json", binary=OLD, ok=False)
    assert "care-capable writer required" in error["error"] and counts(DB) == frozen
old_refusal()
backup = OUT / "structural.zip"
run("space", "backup", "--output", str(backup), "--format", "json")
ENV["OBSDOG_HOME"] = str(OUT / "restored-profile")
run("space", "restore", "--backup", str(backup), "--format", "json")
DB = Path(ENV["OBSDOG_HOME"]) / "spaces" / SPACE / "obsdog.db"
assert read(DOC)["markdown"] == state["markdown"]
receipt = run("care", "runs", "--space", SPACE, "--run", heading["run_id"], "--format", "json")
assert receipt["action"] == "insert-heading"
old_refusal()
(OUT / "accepted.json").write_text(json.dumps(dict(checks=["read_only_cli_under_writer", "real_stdio_mcp_under_writer",
    "rollback_only_readiness", "honest_unobserved_fallback", "leading_h1", "midsection_h2", "subtree_retirement",
    "other_parent_move", "noncontiguous_cross_document_lineage", "original_intent_replay",
    "actual_prior_writer_refusal", "backup_restore_preserves_floor"]), indent=2))
print(OUT)
