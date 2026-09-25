"""Behavioral verifier for procmail conditional delivery fork simulator."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from reference_delivery import audit_from_snapshot_path, reference_simulate

APP = Path("/app")
FIXTURES = APP / "fixtures" / "suites"
CLI = "/app/bin/procmail-sim"
RESET = APP / "scripts" / "reset-state.sh"
SNAPSHOT = APP / "state" / "delivery-snapshot.json"
OUTPUT = APP / "output" / "procmail-audit.json"
LIB = APP / "lib" / "procmail-sim"
BROKEN_LIB = Path(__file__).resolve().parent / "broken_lib" / "procmail-sim"
GOLDEN_LIB = Path(__file__).resolve().parent / "golden_lib" / "procmail-sim"
HIDDEN = Path(__file__).resolve().parent / "fixtures" / "hidden_suites"
VERIFIER_SEED = os.environ.get("VERIFIER_SEED", "procmail-conditional-delivery-fork-repair")

BUNDLED = [
    "001-basic-delivery",
    "002-nested-lock-scope",
    "003-hostname-condition",
    "004-continue-headers",
    "005-orgmail-fork",
]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def simulate(suite: Path, snap: Path | None = None) -> subprocess.CompletedProcess[str]:
    target = snap or SNAPSHOT
    return run(
        [
            CLI,
            "simulate",
            "--suite",
            str(suite),
            "--snapshot",
            str(target),
        ]
    )


def audit(snap: Path, out: Path | None = None) -> subprocess.CompletedProcess[str]:
    target = out or OUTPUT
    return run([CLI, "audit", "--snapshot", str(snap), "--output", str(target)])


def install_lib_module(name: str, *, golden: bool) -> None:
    src_dir = GOLDEN_LIB if golden else BROKEN_LIB
    src = src_dir / name
    dest = LIB / name
    data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    dest.write_bytes(data)


def restore_broken_lib() -> None:
    for src in BROKEN_LIB.glob("*.sh"):
        install_lib_module(src.name, golden=False)


def assert_snapshot_matches_reference(suite: Path) -> dict:
    reset()
    proc = simulate(suite)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    want = reference_simulate(suite)
    assert got["suite_id"] == want["suite_id"]
    assert got["environment"] == want["environment"]
    assert got["deliveries"] == want["deliveries"]
    assert got["skipped_recipes"] == want["skipped_recipes"]
    assert got["stats"] == want["stats"]
    return got


def test_contract_output_paths_exist() -> None:
    """Simulate writes /app/state/delivery-snapshot.json; audit writes /app/output/procmail-audit.json; locks under /app/state/locks/."""
    reset()
    proc = simulate(FIXTURES / "001-basic-delivery")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert Path("/app/state/delivery-snapshot.json").is_file()
    assert Path("/app/state/locks/").is_dir()
    proc = audit(Path("/app/state/delivery-snapshot.json"), Path("/app/output/procmail-audit.json"))
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert Path("/app/output/procmail-audit.json").is_file()


def test_basic_delivery_matches_reference() -> None:
    """Bundled 001: simple regex delivery."""
    assert_snapshot_matches_reference(FIXTURES / "001-basic-delivery")


def test_nested_lock_scope_matches_reference() -> None:
    """Bundled 002: nested lockfile scope must not false busy."""
    assert_snapshot_matches_reference(FIXTURES / "002-nested-lock-scope")


def test_hostname_condition_matches_reference() -> None:
    """Bundled 003: HOSTNAME token must not read HOST."""
    assert_snapshot_matches_reference(FIXTURES / "003-hostname-condition")


def test_continue_headers_matches_reference() -> None:
    """Bundled 004: hc continue plus deliver.sh dedup; duplicate_suppressed stays 0 when mboxes differ."""
    assert_snapshot_matches_reference(FIXTURES / "004-continue-headers")


def test_orgmail_fork_matches_reference() -> None:
    """Bundled 005: nested fork must honor ORGMAIL fallback."""
    assert_snapshot_matches_reference(FIXTURES / "005-orgmail-fork")


def test_hidden_chained_suite_matches_reference() -> None:
    """Hidden suite combines hostname, nested lock, and orgmail fork."""
    assert_snapshot_matches_reference(HIDDEN / "101-hidden-chained")


def test_two_stage_audit_reads_snapshot_only() -> None:
    """Audit must export snapshot fields without re-running simulate."""
    suite = FIXTURES / "004-continue-headers"
    reset()
    snap = reference_simulate(suite)
    snap["skipped_recipes"] = [{"recipe_id": "r9.9", "reason": "lock_busy"}]
    SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    proc = audit(SNAPSHOT, OUTPUT)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    got = json.loads(OUTPUT.read_text(encoding="utf-8"))
    want = audit_from_snapshot_path(SNAPSHOT)
    assert got == want


def test_audit_includes_skipped_recipes() -> None:
    """Audit export must copy skipped_recipes from snapshot."""
    restore_broken_lib()
    snap_path = APP / "state" / "audit-snap.json"
    snap = {
        "snapshot_version": 1,
        "suite_id": "audit-skip-probe",
        "environment": {"HOST": "h", "HOSTNAME": "hn", "ORGMAIL": "/var/mail/f.mbox"},
        "deliveries": [],
        "skipped_recipes": [{"recipe_id": "r2.1", "reason": "lock_busy"}],
        "stats": {
            "messages_total": 1,
            "recipes_evaluated": 2,
            "recipes_skipped": 1,
            "deliveries_count": 0,
            "lock_serializations": 1,
            "orgmail_fallbacks": 0,
            "duplicate_suppressed": 0,
        },
    }
    snap_path.write_text(json.dumps(snap), encoding="utf-8")
    install_lib_module("audit_export.sh", golden=False)
    proc = audit(snap_path, OUTPUT)
    assert proc.returncode == 0
    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert report["skipped_recipes"] == []
    install_lib_module("audit_export.sh", golden=True)
    proc = audit(snap_path, OUTPUT)
    assert proc.returncode == 0
    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert report["skipped_recipes"] == snap["skipped_recipes"]
    install_lib_module("audit_export.sh", golden=True)


def test_hidden_fixture_not_in_image() -> None:
    """Hidden procmailrc must not ship in the Docker image."""
    assert not (APP / "fixtures" / "hidden_suites").exists()


def test_partial_hostname_fix_fails_hidden() -> None:
    """Patching only env.sh must not pass hidden chained suite."""
    restore_broken_lib()
    install_lib_module("env.sh", golden=True)
    reset()
    proc = simulate(HIDDEN / "101-hidden-chained")
    assert proc.returncode == 0
    got = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    want = reference_simulate(HIDDEN / "101-hidden-chained")
    assert got != want


def test_partial_lock_fix_fails_orgmail() -> None:
    """Lock-only fix must not restore ORGMAIL fallback on bundled 005."""
    restore_broken_lib()
    install_lib_module("lock.sh", golden=True)
    reset()
    proc = simulate(FIXTURES / "005-orgmail-fork")
    assert proc.returncode == 0
    got = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    want = reference_simulate(FIXTURES / "005-orgmail-fork")
    assert got["deliveries"] != want["deliveries"]


def test_seed_mutated_envelope_address() -> None:
    """Mutated Message-ID suffix must change delivery graph vs static guess."""
    suite = FIXTURES / "001-basic-delivery"
    digest = hashlib.sha256(VERIFIER_SEED.encode()).hexdigest()[:6]
    tmp = Path("/tmp") / f"mut-suite-{digest}"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(suite, tmp)
    mbox = tmp / "messages.mbox"
    text = mbox.read_text(encoding="utf-8")
    mbox.write_text(text.replace("msg001", f"msg001-{digest}"), encoding="utf-8")
    assert_snapshot_matches_reference(tmp)
