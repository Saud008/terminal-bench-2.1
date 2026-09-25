"""
Verifier for vicireplay strongSwan VICI SA rekey order replay.

Independent reference_replay mirrors /app/docs policy contracts.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

APP = Path("/app")
CLI = Path("/usr/local/bin/vicireplay")
TRACES = APP / "fixtures" / "traces"
HIDDEN = Path("/opt/verifier-fixtures/traces")
OUTPUT = APP / "output"
SNAPSHOT = APP / "state" / "rekey-snapshot.json"
MANIFEST = APP / "state" / "rekey.manifest"
RESET = APP / "scripts" / "reset-state.sh"
BROKEN = Path("/opt/verifier-broken-vicireplay")
BROKEN_FALLBACK = Path(__file__).resolve().parent / "broken_lib"
PATCHES = Path(__file__).resolve().parent / "patches"

REJECT_REASONS = frozenset(
    {
        "rekey_before_delete_ack",
        "selector_narrowed",
        "uid_reused",
        "seq_not_monotonic",
    }
)

PATCH_TARGETS = {
    "rekey": APP / "internal/fsm/rekey.go",
    "selectors": APP / "internal/childsa/selectors.go",
    "uidmap": APP / "internal/ikesa/uidmap.go",
    "log": APP / "internal/sequence/log.go",
    "publish": APP / "internal/export/publish.go",
    "engine": APP / "internal/replay/engine.go",
}

BROKEN_FILES = {
    "rekey": "rekey.go",
    "selectors": "selectors.go",
    "uidmap": "uidmap.go",
    "log": "log.go",
    "publish": "publish.go",
    "engine": "engine.go",
}

PROTECTED_SHA256: dict[str, str] = {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _populate_hashes() -> None:
    for path in sorted(TRACES.glob("*.jsonl")):
        PROTECTED_SHA256[path.name] = _sha256(path)


_populate_hashes()


def _reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def _broken_root() -> Path:
    return BROKEN if BROKEN.is_dir() else BROKEN_FALLBACK


def _build() -> subprocess.CompletedProcess[str]:
    for path in PATCH_TARGETS.values():
        os.utime(path, None)
    env = {**os.environ, "PATH": "/usr/local/go/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
    return subprocess.run(
        ["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/vicireplay"],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=600,
        env=env,
    )


def _snapshot_sources() -> dict[str, str]:
    return {name: path.read_text(encoding="utf-8") for name, path in PATCH_TARGETS.items()}


def _restore_sources(saved: dict[str, str]) -> None:
    for name, content in saved.items():
        PATCH_TARGETS[name].write_text(content, encoding="utf-8")
        os.utime(PATCH_TARGETS[name], None)


def _restore_broken_sources() -> None:
    root = _broken_root()
    for name, dest in PATCH_TARGETS.items():
        shutil.copyfile(root / BROKEN_FILES[name], dest)
        os.utime(dest, None)


def _install_patch(name: str) -> None:
    dest = PATCH_TARGETS[name]
    shutil.copyfile(PATCHES / f"golden_{name}.go", dest)
    os.utime(dest, None)


@contextmanager
def _patched_module(name: str):
    saved = _snapshot_sources()
    try:
        _restore_broken_sources()
        _install_patch(name)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        yield
    finally:
        _restore_sources(saved)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout


def _load_trace(path: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        events.append(json.loads(line))
    trace_id = path.stem
    return {"trace_id": trace_id, "gateway_id": "gw-local", "events": events}


def _initiator_offset() -> int:
    raw = os.environ.get("VERIFIER_INITIATOR_OFFSET", "")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return 0


def _table_suffix() -> str:
    return os.environ.get("VERIFIER_TABLE_SUFFIX", "") or "default"


def _normalize_trace(tr: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(tr)
    offset = _initiator_offset()
    for ev in out["events"]:
        if ev.get("ike_unique_id"):
            ev["ike_unique_id"] = int(ev["ike_unique_id"]) + offset
        if ev.get("child_unique_id"):
            ev["child_unique_id"] = int(ev["child_unique_id"]) + offset
    return out


def _covers(wider: str, narrow: str) -> bool:
    if wider == narrow:
        return True
    if len(wider) > len(narrow) and wider[len(narrow)] == "/":
        if wider[: len(narrow)] == narrow:
            return True
    return False


def _union(a: list[str], b: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in a + b:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _superset_ok(old_ts: list[str], merged: list[str]) -> bool:
    for o in old_ts:
        if not any(_covers(n, o) for n in merged):
            return False
    return True


def reference_replay(tr: dict[str, Any]) -> dict[str, Any]:
    tr = _normalize_trace(tr)
    pending_delete: set[int] = set()
    ike_in_use: set[int] = set()
    last_seq = 0
    children: dict[int, dict[str, Any]] = {}
    active_spi = 0
    verdicts: list[dict[str, Any]] = []

    for idx, ev in enumerate(tr["events"]):
        rec: dict[str, Any] = {
            "event_index": idx,
            "log_seq": ev["log_seq"],
            "offset_ms": ev["offset_ms"],
            "event_type": ev["type"],
            "order_ok": True,
            "selectors_ok": True,
            "uid_ok": True,
            "seq_monotonic": True,
            "accepted": True,
            "active_spi_out": 0,
        }
        seq = int(ev["log_seq"])
        if seq <= last_seq:
            rec["seq_monotonic"] = False
            rec["accepted"] = False
            rec["reject_reason"] = "seq_not_monotonic"
        else:
            last_seq = seq

        et = ev["type"]
        if et == "ike_up":
            uid = int(ev["ike_unique_id"])
            if uid in ike_in_use:
                rec["uid_ok"] = False
                rec["accepted"] = False
                rec["reject_reason"] = "uid_reused"
            else:
                ike_in_use.add(uid)
        elif et == "ike_down":
            ike_in_use.discard(int(ev["ike_unique_id"]))
        elif et == "child_up":
            cid = int(ev["child_unique_id"])
            children[cid] = {
                "spi_in": int(ev["spi_in"]),
                "spi_out": int(ev["spi_out"]),
                "local_ts": list(ev.get("local_ts", [])),
                "remote_ts": list(ev.get("remote_ts", [])),
                "deleted": False,
                "active": True,
            }
            active_spi = int(ev["spi_out"])
        elif et == "child_delete_request":
            pending_delete.add(int(ev["req_id"]))
        elif et == "child_delete_response":
            pending_delete.discard(int(ev["req_id"]))
            cid = int(ev["child_unique_id"])
            if cid in children:
                children[cid]["deleted"] = True
                children[cid]["active"] = False
            active_spi = 0
            for c in children.values():
                if c["active"] and not c["deleted"]:
                    active_spi = int(c["spi_out"])
        elif et == "child_rekey":
            if pending_delete:
                rec["order_ok"] = False
                rec["accepted"] = False
                rec["reject_reason"] = "rekey_before_delete_ack"
        elif et == "child_rekey_done":
            cid = int(ev["child_unique_id"])
            old = children.get(cid)
            if old:
                loc = _union(old["local_ts"], list(ev.get("local_ts", [])))
                rem = _union(old["remote_ts"], list(ev.get("remote_ts", [])))
                if not _superset_ok(old["local_ts"], loc) or not _superset_ok(old["remote_ts"], rem):
                    rec["selectors_ok"] = False
                    rec["accepted"] = False
                    rec["reject_reason"] = "selector_narrowed"
                old["deleted"] = True
                old["active"] = False
                children[cid] = old
            new_child = {
                "spi_in": int(ev["spi_in"]),
                "spi_out": int(ev["spi_out"]),
                "local_ts": _union(old["local_ts"], list(ev.get("local_ts", []))) if old else list(ev.get("local_ts", [])),
                "remote_ts": _union(old["remote_ts"], list(ev.get("remote_ts", []))) if old else list(ev.get("remote_ts", [])),
                "deleted": False,
                "active": True,
            }
            children[cid] = new_child
            active_spi = int(ev["spi_out"])

        if rec["accepted"] and not rec.get("reject_reason"):
            rec["active_spi_out"] = active_spi
        elif verdicts:
            rec["active_spi_out"] = verdicts[-1]["active_spi_out"]
        else:
            rec["active_spi_out"] = active_spi
        verdicts.append(rec)

    active_spi = 0
    for c in children.values():
        if c["active"] and not c["deleted"]:
            active_spi = int(c["spi_out"])

    violations = sum(
        1 for v in verdicts if not v.get("accepted") and v.get("reject_reason") in REJECT_REASONS
    )
    return {
        "snapshot_version": 1,
        "table_suffix": _table_suffix(),
        "trace_id": tr["trace_id"],
        "initiator_offset": _initiator_offset(),
        "verdicts": verdicts,
        "active_spi_out": active_spi,
        "rekey_violation_count": violations,
    }


def _replay(trace_path: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": "/usr/local/go/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
    return subprocess.run(
        [str(CLI), "replay", "--trace", str(trace_path), "--output", str(output_path)],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )


def _assert_matches_reference(report: dict[str, Any], trace_path: Path) -> None:
    tr = _load_trace(trace_path)
    expected = reference_replay(tr)
    assert report["trace_id"] == expected["trace_id"]
    assert report["table_suffix"] == expected["table_suffix"]
    assert report["initiator_offset"] == expected["initiator_offset"]
    assert report["active_spi_out"] == expected["active_spi_out"]
    assert report["rekey_violation_count"] == expected["rekey_violation_count"]
    assert report.get("export_source") == "staging_manifest"
    assert len(report["verdicts"]) == len(expected["verdicts"])
    keys = (
        "event_index",
        "log_seq",
        "offset_ms",
        "event_type",
        "order_ok",
        "selectors_ok",
        "uid_ok",
        "seq_monotonic",
        "accepted",
        "reject_reason",
        "active_spi_out",
    )
    for got, want in zip(report["verdicts"], expected["verdicts"], strict=True):
        for key in keys:
            if key == "reject_reason":
                if want.get("reject_reason"):
                    assert got.get("reject_reason") == want.get("reject_reason")
            else:
                assert got.get(key) == want.get(key), f"{trace_path.name} idx {got['event_index']} {key}"


@pytest.fixture(autouse=True)
def _auto_reset():
    _reset()
    yield
    _reset()


def test_cli_builds():
    """vicireplay must compile before replay tests run."""
    proc = _build()
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.mark.parametrize("trace_file", sorted(p.name for p in TRACES.glob("*.jsonl")))
def test_bundled_trace_matches_reference(trace_file: str):
    """Every bundled JSONL trace replay must match independent reference policy."""
    trace_path = TRACES / trace_file
    out_path = OUTPUT / f"report-{trace_file}"
    proc = _replay(trace_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert SNAPSHOT.is_file(), "staging snapshot missing"
    assert MANIFEST.is_file(), "staging manifest missing"
    report = json.loads(out_path.read_text(encoding="utf-8"))
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert report["verdicts"] == snap["verdicts"]
    assert report["active_spi_out"] == snap["active_spi_out"]
    _assert_matches_reference(report, trace_path)


@pytest.mark.parametrize(
    "trace_file",
    ["hidden-overlap-spi-rekey.jsonl", "hidden-order-selector-chain.jsonl"],
)
def test_hidden_trace_matches_reference(trace_file: str):
    """Hidden traces under /opt/verifier-fixtures must match reference replay."""
    trace_path = HIDDEN / trace_file
    out_path = OUTPUT / f"report-hidden-{trace_file}"
    proc = _replay(trace_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    _assert_matches_reference(report, trace_path)


def test_fixture_integrity():
    """Bundled trace files must remain unchanged."""
    for name, digest in PROTECTED_SHA256.items():
        assert _sha256(TRACES / name) == digest


def test_export_reads_staging_only():
    """Report export_source must be staging_manifest."""
    trace_path = TRACES / "001-fresh-child.jsonl"
    out_path = OUTPUT / "report-staging-source.json"
    proc = _replay(trace_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["export_source"] == "staging_manifest"


def test_staging_snapshot_written():
    """Replay must persist rekey-snapshot.json with active_spi_out."""
    trace_path = TRACES / "006-clean-rekey-success.jsonl"
    out_path = OUTPUT / "report-snapshot-check.json"
    proc = _replay(trace_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    expected = reference_replay(_load_trace(trace_path))
    assert snap["active_spi_out"] == expected["active_spi_out"]


def test_initiator_offset_env():
    """VERIFIER_INITIATOR_OFFSET must shift unique ids in replay."""
    os.environ["VERIFIER_INITIATOR_OFFSET"] = "1000"
    try:
        trace_path = TRACES / "001-fresh-child.jsonl"
        out_path = OUTPUT / "report-offset.json"
        proc = _replay(trace_path, out_path)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(out_path.read_text(encoding="utf-8"))
        assert report["initiator_offset"] == 1000
    finally:
        os.environ.pop("VERIFIER_INITIATOR_OFFSET", None)


def test_rekey_gate_only_patch_insufficient():
    """Fixing rekey gate alone must still fail /opt/verifier-fixtures order+selector chain."""
    hidden = HIDDEN / "hidden-order-selector-chain.jsonl"
    with _patched_module("rekey"):
        proc = _replay(hidden, OUTPUT / "partial-rekey-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-rekey-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)


def test_selectors_only_patch_insufficient():
    """Selector widen patch alone must still fail /opt/verifier-fixtures overlap SPI rekey."""
    hidden = HIDDEN / "hidden-overlap-spi-rekey.jsonl"
    with _patched_module("selectors"):
        proc = _replay(hidden, OUTPUT / "partial-selectors-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-selectors-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)


def test_uidmap_only_patch_insufficient():
    """IKE unique-id map patch alone must still fail selector-narrow bundled trap."""
    with _patched_module("uidmap"):
        proc = _replay(TRACES / "003-selector-narrow-on-rekey.jsonl", OUTPUT / "partial-uidmap-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-uidmap-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, TRACES / "003-selector-narrow-on-rekey.jsonl")


def test_sequence_log_only_patch_insufficient():
    """Sequence log patch alone must still fail rekey-before-delete-ack trap."""
    with _patched_module("log"):
        proc = _replay(TRACES / "002-rekey-before-delete-ack.jsonl", OUTPUT / "partial-log-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-log-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, TRACES / "002-rekey-before-delete-ack.jsonl")


def test_engine_only_patch_insufficient():
    """Replay engine patch alone must still fail uid-reuse bundled trap."""
    with _patched_module("engine"):
        proc = _replay(TRACES / "004-uid-reuse.jsonl", OUTPUT / "partial-engine-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-engine-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, TRACES / "004-uid-reuse.jsonl")


def test_report_reject_reason_enum():
    """Reject reasons on failure traces must stay inside the documented enum."""
    trace_path = TRACES / "002-rekey-before-delete-ack.jsonl"
    out_path = OUTPUT / "report-reject-enum.json"
    proc = _replay(trace_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    for row in report.get("verdicts", []):
        reason = row.get("reject_reason")
        if reason:
            assert reason in REJECT_REASONS


def test_manifest_export_source_field():
    """Staging manifest must declare export_source staging_manifest after replay."""
    trace_path = TRACES / "001-fresh-child.jsonl"
    out_path = OUTPUT / "report-manifest-source.json"
    proc = _replay(trace_path, out_path)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest.get("export_source") == "staging_manifest" or (
        json.loads(out_path.read_text(encoding="utf-8")).get("export_source") == "staging_manifest"
    )


def test_decoy_vici_wrap_alone_insufficient():
    """Patching decoy vici wrap helper must not fix export verdicts."""
    wrap_path = APP / "internal" / "vici" / "wrap.go"
    saved_wrap = wrap_path.read_text(encoding="utf-8")
    saved_sources = _snapshot_sources()
    try:
        _restore_broken_sources()
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        wrap_path.write_text(saved_wrap.replace("vici:", "fixed:"), encoding="utf-8")
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        proc = _replay(TRACES / "002-rekey-before-delete-ack.jsonl", OUTPUT / "decoy-wrap.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "decoy-wrap.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, TRACES / "002-rekey-before-delete-ack.jsonl")
    finally:
        wrap_path.write_text(saved_wrap, encoding="utf-8")
        _restore_sources(saved_sources)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout


def test_export_publish_only_patch_insufficient():
    """Fixing export publish alone must not fix replay staging written by the engine."""
    hidden = HIDDEN / "hidden-overlap-spi-rekey.jsonl"
    with _patched_module("publish"):
        proc = _replay(hidden, OUTPUT / "partial-publish-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "partial-publish-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)


def test_ingest_normalization_only_insufficient():
    """Touching ingest normalization alone must not fix replay FSM violations."""
    ingest_path = APP / "internal" / "ingest" / "trace.go"
    saved_ingest = ingest_path.read_text(encoding="utf-8")
    saved_sources = _snapshot_sources()
    hidden = HIDDEN / "hidden-order-selector-chain.jsonl"
    try:
        _restore_broken_sources()
        ingest_path.write_text(saved_ingest.rstrip() + "\n// ingest path verified\n", encoding="utf-8")
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        proc = _replay(hidden, OUTPUT / "ingest-touch-only.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "ingest-touch-only.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, hidden)
    finally:
        ingest_path.write_text(saved_ingest, encoding="utf-8")
        _restore_sources(saved_sources)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout


def test_decoy_merge_apply_alone_insufficient():
    """Patching decoy merge helper must not fix selector widening on rekey."""
    merge_path = APP / "internal" / "merge" / "apply.go"
    saved_merge = merge_path.read_text(encoding="utf-8")
    saved_sources = _snapshot_sources()
    try:
        _restore_broken_sources()
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        merge_path.write_text(
            saved_merge.replace("legacy merge helper", "legacy merge helper (patched)"),
            encoding="utf-8",
        )
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
        proc = _replay(TRACES / "003-selector-narrow-on-rekey.jsonl", OUTPUT / "decoy-merge.json")
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads((OUTPUT / "decoy-merge.json").read_text(encoding="utf-8"))
        with pytest.raises(AssertionError):
            _assert_matches_reference(report, TRACES / "003-selector-narrow-on-rekey.jsonl")
    finally:
        merge_path.write_text(saved_merge, encoding="utf-8")
        _restore_sources(saved_sources)
        proc = _build()
        assert proc.returncode == 0, proc.stderr or proc.stdout
