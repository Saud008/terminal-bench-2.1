"""Behavioral verifier for dnsmasq authoritative renewal skew ledger workflow."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pytest

from dhcp_reference_independent import identity_key, mutate_mac, replay_log

APP = Path("/app")
CLI = "/usr/local/bin/dnsmasqledger"
FIXTURES = APP / "fixtures/replay"
HIDDEN = Path("/opt/verifier-fixtures/replay")
OUT_PATH = "/app/output/lease-report.json"
SNAPSHOT_PATH = "/app/state/lease-snapshot.json"
CKPT_STATE_PREFIX = "/app/state/ckpt-"
OUT = Path(OUT_PATH)
SNAPSHOT = Path(SNAPSHOT_PATH)
DB = APP / "work/leases.db"
RESET = APP / "scripts/reset-state.sh"
SEED = os.environ.get("VERIFIER_SEED", "dnsmasq-lease-seed-8")

BUNDLED = [
    "001-base.jsonl",
    "002-renewal-skew.jsonl",
    "003-duid-collision.jsonl",
    "004-decline-tentative.jsonl",
    "005-ack-replay.jsonl",
    "006-ip-change-checkpoint.jsonl",
    "007-release.jsonl",
    "008-multi-renew.jsonl",
]

HIDDEN_FIXTURES = [
    "da1915b9_hidden-decline-renew.jsonl",
    "da1915b9_hidden-checkpoint-dns.jsonl",
]

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reset() -> None:
    proc = subprocess.run(["bash", str(RESET)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build() -> None:
    proc = subprocess.run(
        ["go", "build", "-mod=readonly", "-o", CLI, "./cmd/dnsmasqledger"],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_replay(log_path: Path) -> dict:
    reset()
    proc = subprocess.run(
        [
            CLI,
            "replay",
            "--log",
            str(log_path),
            "--output",
            str(OUT),
            "--db",
            str(DB),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert OUT.is_file(), "lease-report.json missing"
    assert SNAPSHOT.is_file(), "lease-snapshot.json missing"
    assert DB.is_file(), "leases.db missing"
    return json.loads(OUT.read_text(encoding="utf-8"))


def assert_report_matches_reference(log_path: Path, report: dict) -> None:
    ref = replay_log(log_path)
    assert report["now_sec"] == ref["now_sec"], "now_sec mismatch"
    assert report["dns_forward"] == ref["dns_forward"], "dns_forward mismatch"
    assert report["checkpoint_seq"] == ref["checkpoint_seq"], "checkpoint mismatch"
    assert report["tentative_count"] == ref["tentative_count"], "tentative_count mismatch"
    assert report["active_leases"] == ref["active_leases"], "active_leases mismatch"


def sqlite_rows() -> list[tuple]:
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(
            "SELECT identity_key, mac, duid, iaid, hostname, ip, expires_sec, authoritative "
            "FROM leases ORDER BY identity_key"
        )
        return cur.fetchall()
    finally:
        con.close()


@pytest.fixture(scope="session", autouse=True)
def _ensure_build() -> None:
    build()


@pytest.fixture(autouse=True)
def _clean_state() -> None:
    reset()


def test_tda1915_module_docstring_contract_paths() -> None:
    """Module docstring maps DHCP lease verifier contract paths."""
    assert "dnsmasqledger" in __doc__ or "Behavioral verifier" in __doc__


@pytest.mark.parametrize("fixture", BUNDLED)
def test_tda1915_dhcp_bundled_log_matches_independent_math(fixture: str) -> None:
    """Each bundled DHCP JSONL replay matches independent reference math."""
    log_path = FIXTURES / fixture
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


@pytest.mark.parametrize("fixture", HIDDEN_FIXTURES)
def test_tda1915_opt_verifier_dhcp_log_matches_independent_math(fixture: str) -> None:
    """Hidden DHCP replay logs under /opt/verifier-fixtures/ match reference."""
    log_path = HIDDEN / fixture
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


def test_tda1915_lease_snapshot_forward_table() -> None:
    """Replay writes /app/state/lease-snapshot.json with dns_forward matching /app/output/lease-report.json export."""
    report = run_replay(FIXTURES / "001-base.jsonl")
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["dns_forward"] == report["dns_forward"]
    assert snap["now_sec"] == report["now_sec"]


def test_tda1915_authoritative_lease_db_rows() -> None:
    """SQLite leases.db mirrors authoritative active leases from report."""
    report = run_replay(FIXTURES / "003-duid-collision.jsonl")
    rows = sqlite_rows()
    assert len(rows) == len(report["active_leases"])
    for rep_row, sql_row in zip(report["active_leases"], rows, strict=True):
        assert rep_row["identity_key"] == sql_row[0]
        assert rep_row["ip"] == sql_row[5]
        assert sql_row[7] == 1


def test_tda1915_renewal_skew_expiry_anchor() -> None:
    """Renewal-skew fixture requires prior-expiry anchor (not receipt time)."""
    report = run_replay(FIXTURES / "002-renewal-skew.jsonl")
    ref = replay_log(FIXTURES / "002-renewal-skew.jsonl")
    lease = report["active_leases"][0]
    assert lease["expires_sec"] == ref["active_leases"][0]["expires_sec"]
    assert lease["expires_sec"] > report["now_sec"]


def test_tda1915_dhcp_decline_zero_tentative() -> None:
    """Decline hidden fixture must leave zero tentative rows in reference."""
    ref = replay_log(HIDDEN / "da1915b9_hidden-decline-renew.jsonl")
    report = run_replay(HIDDEN / "da1915b9_hidden-decline-renew.jsonl")
    assert ref["tentative_count"] == 0
    assert_report_matches_reference(HIDDEN / "da1915b9_hidden-decline-renew.jsonl", report)


def test_tda1915_dhcp_ckpt_forward_purge() -> None:
    """IP change checkpoint under /app/state/ckpt- must not retain stale DNS forward for old IP."""
    report = run_replay(HIDDEN / "da1915b9_hidden-checkpoint-dns.jsonl")
    assert "ckpt.lan" in report["dns_forward"]
    assert report["dns_forward"]["ckpt.lan"] == "172.16.2.21"
    assert "172.16.2.20" not in report["dns_forward"].values()


def test_tda1915_procedural_mutated_mac_replay() -> None:
    """Mutated MAC in copied fixture prevents hardcoded golden answers."""
    src = FIXTURES / "001-base.jsonl"
    raw = src.read_text(encoding="utf-8")
    mac = mutate_mac(SEED, "aa:bb:cc:00:01:01")
    raw = raw.replace("aa:bb:cc:00:01:01", mac)
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "proc-base.jsonl"
        log_path.write_text(raw, encoding="utf-8")
        report = run_replay(log_path)
        assert report["active_leases"][0]["mac"] == mac
        assert_report_matches_reference(log_path, report)


def test_tda1915_duid_collision_requires_full_identity_tuple() -> None:
    """DUID collision fixture requires mac|duid|iaid identity keys, not MAC-only bindings."""
    report = run_replay(FIXTURES / "003-duid-collision.jsonl")
    ref = replay_log(FIXTURES / "003-duid-collision.jsonl")
    assert len(report["active_leases"]) == len(ref["active_leases"])
    assert len(report["active_leases"]) >= 2
    keys = {row["identity_key"] for row in report["active_leases"]}
    assert len(keys) == len(report["active_leases"])
    assert_report_matches_reference(FIXTURES / "003-duid-collision.jsonl", report)


def test_tda1915_tb3_dhcp_log_directory_override() -> None:
    """TB3_REPLAY_DIR selects alternate DHCP fixture directory for replay logs."""
    tb3 = os.environ.get("TB3_REPLAY_DIR")
    if not tb3:
        pytest.skip("TB3_REPLAY_DIR not set")
    alt = Path(tb3)
    assert alt.is_dir()
    logs = sorted(alt.glob("*.jsonl"))
    assert logs, "TB3 dir empty"
    report = run_replay(logs[0])
    assert report["events_applied"] > 0


def test_tda1915_identity_key_format_in_report() -> None:
    """Exported identity_key uses mac|duid|iaid tuple per lease contract."""
    report = run_replay(FIXTURES / "001-base.jsonl")
    row = report["active_leases"][0]
    expected = identity_key(row["mac"], row["duid"], row["iaid"])
    assert row["identity_key"] == expected


def test_tda1915_ack_replay_fixture_matches() -> None:
    """005-ack-replay bundled log matches independent reference."""
    log_path = FIXTURES / "005-ack-replay.jsonl"
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


def test_tda1915_multi_renew_fixture_matches() -> None:
    """008-multi-renew bundled log matches independent reference."""
    log_path = FIXTURES / "008-multi-renew.jsonl"
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


def test_tda1915_release_fixture_matches() -> None:
    """007-release bundled log matches independent reference."""
    log_path = FIXTURES / "007-release.jsonl"
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


def test_tda1915_decline_tentative_bundled_matches() -> None:
    """004-decline-tentative bundled log matches independent reference."""
    log_path = FIXTURES / "004-decline-tentative.jsonl"
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


def test_tda1915_ip_change_checkpoint_bundled_matches() -> None:
    """006-ip-change-checkpoint bundled log matches independent reference."""
    log_path = FIXTURES / "006-ip-change-checkpoint.jsonl"
    report = run_replay(log_path)
    assert_report_matches_reference(log_path, report)


def test_tda1915_events_applied_positive() -> None:
    """Replay reports positive events_applied for base dhcp log."""
    report = run_replay(FIXTURES / "001-base.jsonl")
    assert report["events_applied"] > 0
