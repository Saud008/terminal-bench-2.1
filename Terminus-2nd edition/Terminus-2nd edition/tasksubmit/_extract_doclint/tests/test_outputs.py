"""Behavioral verifier for term-lsp document version-admission and snapshot export."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from lsp_client import LspClient
from reference_lsp import export_snapshot, mutate_changes, replay_steps

APP = Path("/app")
TEST_ROOT = Path(os.environ.get("TEST_DIR", "/tests"))
SOURCES = APP / "fixtures" / "sources"
BATCHES = APP / "fixtures" / "batches" / "core-sequences.jsonl"
CATALOG = json.loads((APP / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
SEEDS = json.loads((APP / "fixtures" / "seeds.json").read_text(encoding="utf-8"))["seeds"]
MODEL = APP / "crates" / "docmodel" / "src"
SYNC = APP / "crates" / "docsync" / "src"
EXPORT = APP / "crates" / "docexport" / "src"
BROKEN_MODEL = Path(
    os.environ.get("VERIFIER_BROKEN_MODEL", str(TEST_ROOT / "verifier-broken-docmodel"))
)
BROKEN_SYNC = Path(
    os.environ.get("VERIFIER_BROKEN_SYNC", str(TEST_ROOT / "verifier-broken-docsync"))
)
BROKEN_EXPORT = Path(
    os.environ.get("VERIFIER_BROKEN_EXPORT", str(TEST_ROOT / "verifier-broken-docexport"))
)
GOLDEN = TEST_ROOT / "verifier-golden"
TB3 = Path("/opt/verifier-fixtures/lsp-doclint")
LSP_BIN = Path("/usr/local/bin/term-lsp")
LSP_RELEASE = APP / "target" / "release" / "term-lsp"

MODEL_MODULES = ("utf16", "apply", "buffer")
SYNC_MODULES = ("change", "lifecycle")
EXPORT_MODULES = ("snapshot",)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_fixture_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((APP / "fixtures").rglob("*")):
        if path.is_file():
            out[str(path.relative_to(APP))] = sha256(path)
    return out


PROTECTED = protected_fixture_hashes()


def reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True, cwd=str(APP))


def build_release() -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": "/usr/local/cargo/bin:/usr/local/bin:" + os.environ.get("PATH", ""),
        "CARGO_NET_OFFLINE": "true",
        "CARGO_INCREMENTAL": "0",
    }
    return subprocess.run(
        ["cargo", "build", "--offline", "--release", "--locked", "-p", "term-lsp"],
        cwd=str(APP),
        capture_output=True,
        text=True,
        timeout=900,
        env=env,
    )


def lsp_binary() -> Path:
    return LSP_RELEASE if LSP_RELEASE.is_file() else LSP_BIN


def restore_broken() -> None:
    assert BROKEN_MODEL.is_dir(), "verifier baseline docmodel not mounted"
    assert BROKEN_SYNC.is_dir(), "verifier baseline docsync not mounted"
    assert BROKEN_EXPORT.is_dir(), "verifier baseline docexport not mounted"
    for mod in MODEL_MODULES:
        shutil.copy2(BROKEN_MODEL / f"{mod}.rs", MODEL / f"{mod}.rs")
    for mod in SYNC_MODULES:
        shutil.copy2(BROKEN_SYNC / f"{mod}.rs", SYNC / f"{mod}.rs")
    for mod in EXPORT_MODULES:
        shutil.copy2(BROKEN_EXPORT / f"{mod}.rs", EXPORT / f"{mod}.rs")


def install_golden(modules: set[str]) -> None:
    mapping = {
        "utf16": GOLDEN / "golden_utf16.rs",
        "apply": GOLDEN / "golden_apply.rs",
        "buffer": GOLDEN / "golden_buffer.rs",
        "change": GOLDEN / "golden_change.rs",
        "lifecycle": GOLDEN / "golden_lifecycle.rs",
        "snapshot": GOLDEN / "golden_snapshot.rs",
    }
    targets = {
        "utf16": MODEL / "utf16.rs",
        "apply": MODEL / "apply.rs",
        "buffer": MODEL / "buffer.rs",
        "change": SYNC / "change.rs",
        "lifecycle": SYNC / "lifecycle.rs",
        "snapshot": EXPORT / "snapshot.rs",
    }
    for name in modules:
        shutil.copy2(mapping[name], targets[name])
        os.utime(targets[name], None)


def partial_patch(fn) -> None:
    try:
        restore_broken()
        fn()
    finally:
        restore_broken()
        proc = build_release()
        assert proc.returncode == 0, proc.stderr or proc.stdout


def run_rpc_sequence(uri: str, source_name: str, steps: list[dict], seed: str = "alpha01") -> dict:
    text = (SOURCES / source_name).read_text(encoding="utf-8")
    mutated_steps = []
    for step in steps:
        s = dict(step)
        if s.get("op") == "change":
            s["changes"] = mutate_changes(s.get("changes", []), seed)
        mutated_steps.append(s)

    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text, version=0)
        for step in mutated_steps:
            op = step["op"]
            if op == "change":
                client.did_change(uri, int(step["version"]), step.get("changes", []))
            elif op == "close":
                client.did_close(uri)
            elif op == "export":
                return client.export_snapshot(uri)
        return client.export_snapshot(uri)
    finally:
        client.stop()


def reference_for_scenario(scenario: dict, steps: list[dict], seed: str) -> dict:
    text = (SOURCES / scenario["source"]).read_text(encoding="utf-8")
    mutated = []
    for step in steps:
        s = dict(step)
        if s.get("op") == "change":
            s["changes"] = mutate_changes(s.get("changes", []), seed)
        mutated.append(s)
    return replay_steps(scenario["uri"], text, mutated)


@pytest.fixture(scope="module", autouse=True)
def release_binary_ready() -> None:
    reset()
    proc = build_release()
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_fixture_integrity() -> None:
    """Protected fixtures must remain unchanged."""
    current = protected_fixture_hashes()
    assert current == PROTECTED


def test_verifier_baseline_not_baked_into_image() -> None:
    """Partial-fix baselines must come from the verifier mount, not the agent image."""
    assert not Path("/opt/verifier-broken-docmodel").exists()
    assert not Path("/opt/verifier-broken-docsync").exists()
    assert not Path("/opt/verifier-broken-docexport").exists()


def test_repair_targets_module_sources() -> None:
    """Sync contract modules must exist and export still routes through crate APIs."""
    layout = (APP / "docs" / "crate-module-layout.md").read_text(encoding="utf-8")
    assert "docmodel" in layout and "docsync" in layout and "docexport" in layout
    for mod in MODEL_MODULES:
        assert (MODEL / f"{mod}.rs").is_file()
    for mod in SYNC_MODULES:
        assert (SYNC / f"{mod}.rs").is_file()
    assert (EXPORT / "snapshot.rs").is_file()

    scenario = CATALOG["scenarios"][0]
    uri = scenario["uri"]
    text = (SOURCES / scenario["source"]).read_text(encoding="utf-8")
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text)
        client.did_change(
            uri,
            1,
            [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 3}}, "text": "pub"}],
        )
        snap = client.export_snapshot(uri)
        assert snap["text"].startswith("pub")
        assert snap["staging_pending"] == 0
    finally:
        client.stop()


@pytest.mark.parametrize("seed", SEEDS[:3])
def test_batch_sequences_match_reference(seed: str) -> None:
    """RPC replay must match independent reference for catalog scenarios."""
    lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
    for scenario, line in zip(CATALOG["scenarios"], lines[:4], strict=True):
        steps = json.loads(line)["steps"]
        expect = reference_for_scenario(scenario, steps, seed)
        got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, seed)
        assert got["text"] == expect["text"], scenario["name"]
        assert got["version"] == expect["version"], scenario["name"]
        assert got["diagnostics"] == expect["diagnostics"], scenario["name"]
        assert got["staging_pending"] == 0


def test_version_monotonic_under_rapid_changes() -> None:
    """Version must not advance before merged text reflects staged edits."""
    uri = CATALOG["scenarios"][0]["uri"]
    source = CATALOG["scenarios"][0]["source"]
    text = (SOURCES / source).read_text(encoding="utf-8")
    changes = [
        {"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 3}}, "text": "pub"}
    ]
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text)
        client.did_change(uri, 1, changes)
        snap = client.export_snapshot(uri)
        from reference_lsp import Document, export_snapshot as ref_export, handle_did_change as ref_change

        doc = Document(uri=uri, text=text)
        ref_change(doc, 1, changes)
        expect = ref_export(doc)
        assert snap["version"] == expect["version"]
        assert snap["text"] == expect["text"]
        assert snap["staging_pending"] == 0
    finally:
        client.stop()


def test_replay_same_version_not_double_applied() -> None:
    """Identical change batch version must not apply twice."""
    scenario = CATALOG["scenarios"][3]
    lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
    steps = json.loads(lines[4])["steps"]
    expect = reference_for_scenario(scenario, steps, "gamma99")
    got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "gamma99")
    assert got == expect


def test_close_flushes_staging_to_text() -> None:
    """didClose must merge staging before clearing."""
    scenario = CATALOG["scenarios"][3]
    lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
    steps = json.loads(lines[3])["steps"]
    expect = reference_for_scenario(scenario, steps, "beta22")
    got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "beta22")
    assert got["text"] == expect["text"]
    assert "TODO" not in got["text"] or got["diagnostics"]["todo_count"] == expect["diagnostics"]["todo_count"]


def test_emoji_utf16_edit_position() -> None:
    """Surrogate-pair prefix must use UTF-16 offsets."""
    scenario = CATALOG["scenarios"][1]
    lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
    steps = json.loads(lines[1])["steps"]
    expect = reference_for_scenario(scenario, steps, "surro88")
    got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "surro88")
    assert got["text"] == expect["text"]


def test_overlapping_edits_same_batch() -> None:
    """Overlapping edits in one didChange must use end-before-start ordering."""
    scenario = CATALOG["scenarios"][0]
    lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
    steps = json.loads(lines[0])["steps"]
    expect = reference_for_scenario(scenario, steps, "epoch07")
    got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "epoch07")
    assert got["text"] == expect["text"]


def test_export_diagnostics_recomputed_not_snapshot_file() -> None:
    """Diagnostics must come from merged text, not pre-merge buffer."""
    scenario = CATALOG["scenarios"][2]
    uri = scenario["uri"]
    text = (SOURCES / scenario["source"]).read_text(encoding="utf-8")
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text)
        client.did_change(
            uri,
            1,
            [{"range": {"start": {"line": 2, "character": 4}, "end": {"line": 2, "character": 8}}, "text": "DONE"}],
        )
        snap = client.export_snapshot(uri)
        from reference_lsp import Document, handle_did_change as ref_change

        doc = Document(uri=uri, text=text)
        ref_change(
            doc,
            1,
            [{"range": {"start": {"line": 2, "character": 4}, "end": {"line": 2, "character": 8}}, "text": "DONE"}],
        )
        expect = export_snapshot(doc)
        assert snap["diagnostics"] == expect["diagnostics"]
        assert snap["diagnostics"]["todo_count"] == expect["diagnostics"]["todo_count"]
    finally:
        client.stop()


def test_server_restart_mid_edit_sequence() -> None:
    """Restarting the server mid-sequence after flush preserves committed text."""
    scenario = CATALOG["scenarios"][0]
    uri = scenario["uri"]
    text = (SOURCES / scenario["source"]).read_text(encoding="utf-8")
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text)
        client.did_change(
            uri,
            1,
            [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 3}}, "text": "pub"}],
        )
        mid = client.export_snapshot(uri)
    finally:
        client.stop()

    client2 = LspClient(lsp_binary())
    client2.start()
    try:
        client2.did_open(uri, mid["text"], version=mid["version"])
        final = client2.export_snapshot(uri)
        assert final["text"] == mid["text"]
        assert final["version"] == mid["version"]
    finally:
        client2.stop()


def test_staging_pending_before_export_flush() -> None:
    """Staging queue must be non-empty before export merges pending edits."""
    scenario = CATALOG["scenarios"][0]
    uri = scenario["uri"]
    text = (SOURCES / scenario["source"]).read_text(encoding="utf-8")
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text)
        client.did_change(
            uri,
            1,
            [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 3}}, "text": "pub"}],
        )
        snap = client.export_snapshot(uri)
        assert snap["staging_pending"] == 0
        assert snap["text"].startswith("pub")
    finally:
        client.stop()


def test_did_open_honors_supplied_version() -> None:
    """didOpen must seed version from client, not force zero after export."""
    scenario = CATALOG["scenarios"][0]
    uri = scenario["uri"]
    text = (SOURCES / scenario["source"]).read_text(encoding="utf-8")
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text, version=7)
        client.did_change(
            uri,
            8,
            [{"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 3}}, "text": "pub"}],
        )
        snap = client.export_snapshot(uri)
        assert snap["version"] == 8
    finally:
        client.stop()


def test_tb3_hidden_wide_mix_sequence() -> None:
    """TB3 fixture under /opt/verifier-fixtures must match reference replay."""
    spec = json.loads((TB3 / "tb3-wide-mix.json").read_text(encoding="utf-8"))
    scenario = next(s for s in CATALOG["scenarios"] if s["source"] == spec["source"])
    lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
    steps = json.loads(lines[int(spec["batch_line"])])["steps"]
    seed = spec["seed"]
    expect = reference_for_scenario(scenario, steps, seed)
    got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, seed)
    assert got == expect


def test_tb3_hidden_restart_roundtrip() -> None:
    """TB3 fixture verifies restart didOpen preserves exported version."""
    spec = json.loads((TB3 / "tb3-restart-roundtrip.json").read_text(encoding="utf-8"))
    uri = spec["uri"]
    text = (SOURCES / spec["source"]).read_text(encoding="utf-8")
    change = spec["change"]
    client = LspClient(lsp_binary())
    client.start()
    try:
        client.did_open(uri, text)
        client.did_change(uri, int(change["version"]), [change])
        mid = client.export_snapshot(uri)
    finally:
        client.stop()

    client2 = LspClient(lsp_binary())
    client2.start()
    try:
        client2.did_open(uri, mid["text"], version=mid["version"])
        final = client2.export_snapshot(uri)
        assert final["text"] == mid["text"]
        assert final["version"] == mid["version"]
    finally:
        client2.stop()


def test_partial_utf16_only_fails_hidden_emoji() -> None:
    """Patching only utf16 passes ASCII but fails surrogate scenario."""

    def probe() -> None:
        install_golden({"utf16"})
        proc = build_release()
        assert proc.returncode == 0, proc.stderr
        scenario = CATALOG["scenarios"][1]
        lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
        steps = json.loads(lines[1])["steps"]
        expect = reference_for_scenario(scenario, steps, "surro88")
        got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "surro88")
        assert got["text"] != expect["text"]

    partial_patch(probe)


def test_partial_version_only_fails_replay_gate() -> None:
    """Patching only change.rs leaves replay double-apply."""

    def probe() -> None:
        install_golden({"change"})
        proc = build_release()
        assert proc.returncode == 0, proc.stderr
        scenario = CATALOG["scenarios"][3]
        lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
        steps = json.loads(lines[4])["steps"]
        expect = reference_for_scenario(scenario, steps, "gamma99")
        got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "gamma99")
        assert got["text"] != expect["text"]

    partial_patch(probe)


def test_partial_lifecycle_only_fails_close_flush() -> None:
    """Patching only lifecycle merges on close with broken apply ordering."""

    def probe() -> None:
        install_golden({"lifecycle"})
        proc = build_release()
        assert proc.returncode == 0, proc.stderr
        scenario = CATALOG["scenarios"][0]
        lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
        steps = json.loads(lines[0])["steps"]
        mutated = [dict(step) for step in steps if step.get("op") != "export"]
        mutated.insert(-1, {"op": "close"})
        mutated.append({"op": "export"})
        expect = reference_for_scenario(scenario, mutated, "epoch07")
        got = run_rpc_sequence(scenario["uri"], scenario["source"], mutated, "epoch07")
        assert got["text"] != expect["text"]

    partial_patch(probe)


def test_partial_export_only_fails_overlap_batch() -> None:
    """Patching only snapshot.rs still fails epoch07 overlapping edit batch."""

    def probe() -> None:
        install_golden({"snapshot"})
        proc = build_release()
        assert proc.returncode == 0, proc.stderr
        scenario = CATALOG["scenarios"][0]
        lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
        steps = json.loads(lines[0])["steps"]
        expect = reference_for_scenario(scenario, steps, "epoch07")
        got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "epoch07")
        assert got["text"] != expect["text"]

    partial_patch(probe)


def test_partial_apply_only_fails_overlap_batch() -> None:
    """Patching only apply.rs fails overlapping edit batch."""

    def probe() -> None:
        install_golden({"apply"})
        proc = build_release()
        assert proc.returncode == 0, proc.stderr
        scenario = CATALOG["scenarios"][0]
        lines = BATCHES.read_text(encoding="utf-8").strip().splitlines()
        steps = json.loads(lines[0])["steps"]
        expect = reference_for_scenario(scenario, steps, "epoch07")
        got = run_rpc_sequence(scenario["uri"], scenario["source"], steps, "epoch07")
        assert got["text"] != expect["text"]

    partial_patch(probe)
