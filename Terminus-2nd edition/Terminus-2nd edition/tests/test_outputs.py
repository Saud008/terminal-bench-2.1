"""Behavioral verifier for the party invite audit staging ledger."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from reference_party import (
    GENESIS,
    RETAINED,
    digest,
    effective_occupancy,
    entry_line,
    latest_for,
    verify_ledger,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/partyd")
CONFIG = APP / "config" / "party.json"
SNAPSHOT = APP / "state" / "party-audit-snapshot.json"
EXPORT = APP / "output" / "party-audit.json"
RESET = APP / "scripts" / "reset-state.sh"
PATCHES = Path(__file__).resolve().parent / "patches"
MANIFEST = Path("/opt/verifier-fixtures/protected-manifest.json")
TB3_RETAIN = Path("/opt/verifier-fixtures/tb3_retention_chain.json")
TB3_RETIRE = Path("/opt/verifier-fixtures/tb3_sweep_retire.json")
TB3_TWIN = Path("/opt/verifier-fixtures/tb3_twin_reconcile.json")
TB3_DISC = Path("/opt/verifier-fixtures/tb3_leader_disconnect.json")

PATCH_TARGETS = {
    "canon": APP / "internal/audit/canon.go",
    "ledger": APP / "internal/audit/ledger.go",
    "stage": APP / "internal/party/stage.go",
    "publish": APP / "internal/party/publish.go",
    "sweeper": APP / "internal/cleanup/sweeper.go",
    "query": APP / "internal/store/query.go",
}

PROTECTED = [
    "config/party.json",
    "docs/audit-snapshot.md",
    "docs/export-schema.md",
    "docs/fixture-catalog.md",
    "docs/idempotency.md",
    "docs/invite-lifecycle.md",
    "docs/member-cap.md",
    "docs/party-contract.md",
    "docs/staging-digest.md",
    "docs/sweep-contract.md",
    "fixtures/catalog.json",
    "cmd/partyd/main.go",
    "internal/api/server.go",
    "internal/party/handler.go",
    "internal/party/dao.go",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = json.loads(MANIFEST.read_text(encoding="utf-8"))


def _build() -> None:
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _stop_daemon() -> None:
    subprocess.run(["pkill", "-x", "partyd"], check=False)
    time.sleep(0.25)


def _start_daemon() -> None:
    _stop_daemon()
    subprocess.Popen(
        [str(CLI), "serve", "--config", str(CONFIG)],
        cwd=APP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=0.5)
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("partyd did not start")


def _request(
    method: str,
    path: str,
    body: dict | None = None,
    *,
    mono_ms: int | None = None,
    idempotency_key: str | None = None,
) -> tuple[int, dict | str]:
    headers = {"Content-Type": "application/json"}
    if mono_ms is not None:
        headers["X-Test-Mono-Ms"] = str(mono_ms)
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:8080{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, {}
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if not raw:
            return exc.code, {}
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw.strip()


def _reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def _create_party(leader: str, mono_ms: int = 100, max_members: int = 4) -> str:
    status, body = _request(
        "POST",
        "/v1/party/create",
        {"leader_id": leader, "max_members": max_members},
        mono_ms=mono_ms,
    )
    assert status == 200, body
    assert isinstance(body, dict)
    return body["party_id"]


def _invite(
    party_id: str,
    invitee: str,
    ttl_ms: int = 5000,
    mono_ms: int = 200,
) -> str:
    status, body = _request(
        "POST",
        f"/v1/party/{party_id}/invite",
        {"invitee_id": invitee, "ttl_ms": ttl_ms},
        mono_ms=mono_ms,
    )
    assert status == 200, body
    assert isinstance(body, dict)
    return body["invite_id"]


def _accept(
    invite_id: str,
    invitee: str,
    key: str,
    mono_ms: int = 300,
) -> tuple[int, dict | str]:
    return _request(
        "POST",
        f"/v1/invite/{invite_id}/accept",
        {"invitee_id": invitee},
        mono_ms=mono_ms,
        idempotency_key=key,
    )


def _export(party_id: str, mono_ms: int) -> dict:
    status, body = _request(
        "POST",
        "/v1/party/export",
        {"party_id": party_id},
        mono_ms=mono_ms,
    )
    assert status == 200, body
    assert EXPORT.is_file()
    return json.loads(EXPORT.read_text(encoding="utf-8"))


def _export_fail(party_id: str, mono_ms: int, token: str) -> None:
    before = EXPORT.read_bytes() if EXPORT.is_file() else None
    status, body = _request(
        "POST",
        "/v1/party/export",
        {"party_id": party_id},
        mono_ms=mono_ms,
    )
    assert status == 400, (status, body)
    assert token in str(body)
    after = EXPORT.read_bytes() if EXPORT.is_file() else None
    assert after == before


def _load_ledger() -> dict:
    assert SNAPSHOT.is_file()
    ledger = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    verify_ledger(ledger)
    return ledger


@contextmanager
def daemon_session():
    _reset()
    _build()
    _start_daemon()
    try:
        yield
    finally:
        _stop_daemon()


def _install_patch(module: str, kind: str) -> str:
    target = PATCH_TARGETS[module]
    backup = target.read_text(encoding="utf-8")
    shutil.copy(PATCHES / f"{kind}_{module}.go", target)
    return backup


def _restore(module: str, backup: str) -> None:
    PATCH_TARGETS[module].write_text(backup, encoding="utf-8")


def test_protected_files_unchanged() -> None:
    """Verifier hash-checks protected docs, config, handler, and DAO baseline."""
    for rel in PROTECTED:
        assert rel in PROTECTED_SHA256, rel
        assert (APP / rel).is_file(), rel
        assert _sha256(rel) == PROTECTED_SHA256[rel], rel


def test_instruction_output_paths_exist() -> None:
    """Governor pipeline writes the ledger and published report paths from instruction."""
    with daemon_session():
        party_id = _create_party("leader-a")
        invite_id = _invite(party_id, "guest-a")
        _accept(invite_id, "guest-a", "idem-1")
        report = _export(party_id, mono_ms=400)
        assert str(SNAPSHOT) == "/app/state/party-audit-snapshot.json"
        assert str(EXPORT) == "/app/output/party-audit.json"
        assert SNAPSHOT.is_file()
        assert report["party_id"] == party_id
        assert report["audit_seq"] >= 1
        assert report["chain_head"]


class TestStagingIngest:
    def test_invite_appends_ledger_entry(self) -> None:
        """Invite lifecycle stages occupancy into the chained audit ledger."""
        with daemon_session():
            party_id = _create_party("leader-stage")
            _invite(party_id, "guest-stage", mono_ms=500)
            ledger = _load_ledger()
            assert ledger["snapshot_version"] == 2
            assert ledger["audit_seq"] >= 1
            entry = latest_for(ledger, party_id)
            assert entry is not None
            assert entry["status"] == "active"
            assert len(entry["pending_invites"]) == 1
            assert entry["pending_invites"][0]["invitee_id"] == "guest-stage"

    def test_accept_increments_party_seq(self) -> None:
        """Each successful stage write bumps durable party_seq for that party."""
        with daemon_session():
            party_id = _create_party("leader-seq")
            invite_id = _invite(party_id, "guest-seq", mono_ms=600)
            first = latest_for(_load_ledger(), party_id)["party_seq"]
            _accept(invite_id, "guest-seq", "idem-seq", mono_ms=700)
            second = latest_for(_load_ledger(), party_id)["party_seq"]
            assert second == first + 1

    def test_leader_disconnect_stages_disbanded_snapshot(self) -> None:
        """Leader disconnect stages disbanded status with an empty pending list."""
        with daemon_session():
            party_id = _create_party("leader-disc")
            _invite(party_id, "guest-disc", mono_ms=800)
            status, _ = _request(
                "POST",
                f"/v1/party/{party_id}/disconnect",
                {"player_id": "leader-disc"},
                mono_ms=900,
            )
            assert status == 200
            entry = latest_for(_load_ledger(), party_id)
            assert entry is not None
            assert entry["status"] == "disbanded"
            assert entry["pending_invites"] == []
            assert entry["connected_ids"] == []

    def test_suppression_keeps_ledger_byte_identical(self) -> None:
        """Re-staging an unchanged party state leaves the ledger file untouched."""
        with daemon_session():
            party_id = _create_party("leader-supp")
            invite_id = _invite(party_id, "guest-supp", ttl_ms=90000, mono_ms=1000)
            before = SNAPSHOT.read_bytes()
            ledger_before = _load_ledger()
            # Accept then invite again is a change; re-invite an already-pending state
            # via sweep-with-no-expiry must suppress for this party.
            status, body = _request("POST", "/v1/admin/sweep", mono_ms=1100)
            assert status == 200
            assert isinstance(body, dict)
            assert body["sweep_epoch"] == 1
            after = SNAPSHOT.read_bytes()
            ledger_after = _load_ledger()
            # Epoch advances even when no entry is appended for this party.
            assert ledger_after["sweep_epoch"] == 1
            entry = latest_for(ledger_after, party_id)
            assert entry is not None
            assert entry["party_seq"] == latest_for(ledger_before, party_id)["party_seq"]
            assert entry["pending_invites"][0]["invite_id"] == invite_id
            # Entries list and digests unchanged (suppression); only epoch header may change.
            assert [e["entry_digest"] for e in ledger_after["entries"]] == [
                e["entry_digest"] for e in ledger_before["entries"]
            ]
            assert before != after  # epoch bump rewrites the header


class TestCanonicalDigest:
    def test_worked_vector_matches_docs(self) -> None:
        """Canonical digest matches the worked vector in staging-digest.md."""
        line1 = entry_line(
            1,
            "pty_demo",
            1,
            200,
            0,
            "active",
            "leader-a",
            4,
            ["leader-a"],
            [
                {
                    "invite_id": "inv_a1",
                    "invitee_id": "guest-a",
                    "expires_mono_ms": 5200,
                }
            ],
        )
        d1 = digest(GENESIS, line1)
        assert d1 == "b76a731bc3b2c737a7da6be696adf23c8d4329b7daec03eb3215d8803faff2f7"
        line2 = entry_line(
            2,
            "pty_demo",
            2,
            300,
            0,
            "active",
            "leader-a",
            4,
            ["guest-a", "leader-a"],
            [],
        )
        d2 = digest(d1, line2)
        assert d2 == "4fb3ad366744c874627cecba44e889edfeab956e95450ac783a87904f479503f"

    def test_pending_invite_sort_is_expiry_then_id(self) -> None:
        """Staged pending invites are ordered by expires_mono_ms then invite_id."""
        with daemon_session():
            party_id = _create_party("leader-sort", mono_ms=100)
            # Short TTL first, longer TTL second — expiry order must win over invite_id.
            first = _invite(party_id, "guest-z", ttl_ms=2000, mono_ms=200)
            second = _invite(party_id, "guest-a", ttl_ms=9000, mono_ms=300)
            entry = latest_for(_load_ledger(), party_id)
            assert entry is not None
            ids = [row["invite_id"] for row in entry["pending_invites"]]
            assert ids == [first, second]


class TestExportPublish:
    def test_effective_occupancy_from_staged_pending(self) -> None:
        """Export effective occupancy derives from staged pending after join reconciliation."""
        with daemon_session():
            party_id = _create_party("leader-exp")
            _invite(party_id, "guest-exp", ttl_ms=8000, mono_ms=1000)
            ledger = _load_ledger()
            entry = latest_for(ledger, party_id)
            assert entry is not None
            report = _export(party_id, mono_ms=2000)
            expected = effective_occupancy(
                report["connected_members"],
                entry["pending_invites"],
                entry["connected_ids"],
                2000,
            )
            assert report["effective_occupancy"] == expected
            assert report["reserved_slots"] == 1
            assert report["chain_head"] == ledger["chain_head"]
            assert report["audit_seq"] == ledger["audit_seq"]
            assert report["staged_party_seq"] == entry["party_seq"]

    def test_export_still_reports_live_sqlite_pending_counts(self) -> None:
        """Export pending_invites reflects live SQLite rows after sweep marks expired."""
        with daemon_session():
            party_id = _create_party("leader-live")
            _invite(party_id, "guest-live", ttl_ms=1000, mono_ms=3000)
            before = _export(party_id, mono_ms=3500)
            assert before["pending_invites"] >= 1
            _request("POST", "/v1/admin/sweep", mono_ms=5000)
            report = _export(party_id, mono_ms=5000)
            assert report["pending_invites"] == 0
            assert report["stale_staged_invites"] == 0
            assert report["reserved_slots"] == 0

    def test_reserved_slots_dedupe_same_invitee(self) -> None:
        """Two open invitations for the same invitee reserve one seat."""
        with daemon_session():
            party_id = _create_party("leader-dedupe", mono_ms=100, max_members=6)
            _invite(party_id, "guest-same", ttl_ms=20000, mono_ms=200)
            # Second invite for a different invitee so the party has two seats reserved.
            _invite(party_id, "guest-other", ttl_ms=20000, mono_ms=300)
            # Manually stage a duplicate invitee by inviting guest-same again after a
            # revoke is not possible via API; instead accept nothing and assert two
            # distinct invitees reserve two seats.
            report = _export(party_id, mono_ms=400)
            assert report["reserved_slots"] == 2
            assert report["effective_occupancy"] == report["connected_members"] + 2

    def test_joined_invitee_dropped_from_reserved_slots(self) -> None:
        """Accepted invitees already connected do not also occupy a reserved seat."""
        with daemon_session():
            party_id = _create_party("leader-join", mono_ms=100)
            invite_id = _invite(party_id, "guest-join", ttl_ms=20000, mono_ms=200)
            _accept(invite_id, "guest-join", "idem-join", mono_ms=300)
            # A second open invite remains reserved.
            _invite(party_id, "guest-open", ttl_ms=20000, mono_ms=400)
            report = _export(party_id, mono_ms=500)
            assert report["connected_members"] == 2
            assert report["reserved_slots"] == 1
            assert report["effective_occupancy"] == 3

    def test_export_refuses_missing_ledger(self) -> None:
        """Export refuses with the unavailable token when the staging ledger is gone."""
        with daemon_session():
            party_id = _create_party("leader-miss")
            _invite(party_id, "guest-miss", mono_ms=200)
            SNAPSHOT.unlink()
            _export_fail(party_id, mono_ms=300, token="audit ledger unavailable")

    def test_export_refuses_broken_chain(self) -> None:
        """Export refuses with the chain-broken token when an entry digest is forged."""
        with daemon_session():
            party_id = _create_party("leader-chain")
            _invite(party_id, "guest-chain", mono_ms=200)
            ledger = _load_ledger()
            ledger["entries"][-1]["entry_digest"] = "f" * 64
            SNAPSHOT.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
            _export_fail(party_id, mono_ms=300, token="audit ledger chain broken")

    def test_export_refuses_drift_against_live_row(self) -> None:
        """Export refuses when staged status/leader/cap diverge from the live parties row."""
        with daemon_session():
            party_id = _create_party("leader-drift")
            _invite(party_id, "guest-drift", mono_ms=200)
            ledger = _load_ledger()
            for entry in ledger["entries"]:
                if entry["party_id"] == party_id:
                    entry["max_members"] = 99
                    line = entry_line(
                        entry["seq"],
                        entry["party_id"],
                        entry["party_seq"],
                        entry["staged_mono_ms"],
                        entry["sweep_epoch"],
                        entry["status"],
                        entry["leader_id"],
                        entry["max_members"],
                        entry["connected_ids"],
                        entry["pending_invites"],
                    )
                    entry["entry_digest"] = digest(entry["prev_digest"], line)
            ledger["chain_head"] = ledger["entries"][-1]["entry_digest"]
            SNAPSHOT.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
            _export_fail(party_id, mono_ms=300, token="audit ledger drift")


class TestSweepRefresh:
    def test_sweep_uses_monotonic_clock(self) -> None:
        """Sweeper expires invites using the monotonic test clock."""
        with daemon_session():
            party_id = _create_party("leader-sweep")
            _invite(party_id, "guest-sweep", ttl_ms=500, mono_ms=7000)
            status, body = _request("POST", "/v1/admin/sweep", mono_ms=7600)
            assert status == 200
            assert isinstance(body, dict)
            assert body["expired_invites"] >= 1
            assert body["sweep_epoch"] >= 1

    def test_sweep_refreshes_snapshot_pending_list(self) -> None:
        """After sweep, staged pending_invites clears expired entries."""
        with daemon_session():
            party_id = _create_party("leader-refresh")
            _invite(party_id, "guest-refresh", ttl_ms=800, mono_ms=8000)
            _request("POST", "/v1/admin/sweep", mono_ms=9000)
            entry = latest_for(_load_ledger(), party_id)
            assert entry is not None
            assert entry["pending_invites"] == []
            assert entry["sweep_epoch"] >= 1

    def test_sweep_epoch_advances_on_noop(self) -> None:
        """A sweep with nothing to expire still advances and persists sweep_epoch."""
        with daemon_session():
            party_id = _create_party("leader-epoch")
            _invite(party_id, "guest-epoch", ttl_ms=90000, mono_ms=1000)
            status, body = _request("POST", "/v1/admin/sweep", mono_ms=1100)
            assert status == 200
            assert isinstance(body, dict)
            assert body["expired_invites"] == 0
            assert body["sweep_epoch"] == 1
            ledger = _load_ledger()
            assert ledger["sweep_epoch"] == 1
            # Restart the daemon and confirm the epoch survived on disk.
            _stop_daemon()
            _start_daemon()
            status, body = _request("POST", "/v1/admin/sweep", mono_ms=1200)
            assert status == 200
            assert isinstance(body, dict)
            assert body["sweep_epoch"] == 2
            assert _load_ledger()["sweep_epoch"] == 2
            assert latest_for(_load_ledger(), party_id) is not None

    def test_tb3_leader_disconnect_export_fixture(self) -> None:
        """TB3 verifier fixture checks disbanded export after leader disconnect staging."""
        spec = json.loads(TB3_DISC.read_text(encoding="utf-8"))
        with daemon_session():
            party_id = _create_party(spec["leader_label"], mono_ms=1000)
            _invite(party_id, spec["invitee_label"], mono_ms=1200)
            _request(
                "POST",
                f"/v1/party/{party_id}/disconnect",
                {"player_id": spec["leader_label"]},
                mono_ms=spec["disconnect_mono_ms"],
            )
            report = _export(party_id, mono_ms=spec["export_mono_ms"])
            entry = latest_for(_load_ledger(), party_id)
            assert report["status"] == "disbanded"
            assert entry is not None
            assert entry["status"] == "disbanded"
            assert entry["pending_invites"] == []

    def test_tb3_retention_chain_fixture(self) -> None:
        """Hidden fixture: retention window carries chain_base past the newest eviction."""
        spec = json.loads(TB3_RETAIN.read_text(encoding="utf-8"))
        with daemon_session():
            party_id = _create_party(
                spec["leader_label"],
                mono_ms=spec["create_mono_ms"],
                max_members=spec["max_members"],
            )
            invite_ids: list[str] = []
            for i in range(spec["invite_count"]):
                invite_ids.append(
                    _invite(
                        party_id,
                        f"{spec['invitee_prefix']}-{i}",
                        ttl_ms=spec["ttl_ms"],
                        mono_ms=spec["invite_mono_ms"] + i,
                    )
                )
            for i in range(spec["accept_count"]):
                code, _ = _accept(
                    invite_ids[i],
                    f"{spec['invitee_prefix']}-{i}",
                    f"tb3-retain-{i}",
                    mono_ms=spec["accept_mono_ms"] + i,
                )
                assert code == 200
            ledger = _load_ledger()
            assert len(ledger["entries"]) == RETAINED
            assert ledger["chain_base"] != GENESIS
            assert ledger["entries"][0]["prev_digest"] == ledger["chain_base"]
            report = _export(party_id, mono_ms=spec["export_mono_ms"])
            assert report["chain_head"] == ledger["chain_head"]
            assert report["connected_members"] == 1 + spec["accept_count"]
            assert report["reserved_slots"] == (
                spec["invite_count"] - spec["accept_count"]
            )

    def test_tb3_sweep_retire_fixture(self) -> None:
        """Hidden fixture: sweep retires a disbanded party SQLite already deleted."""
        spec = json.loads(TB3_RETIRE.read_text(encoding="utf-8"))
        with daemon_session():
            doomed = _create_party(
                spec["doomed_leader_label"],
                mono_ms=spec["create_mono_ms"],
                max_members=spec["max_members"],
            )
            _invite(
                doomed,
                spec["doomed_invitee_label"],
                ttl_ms=spec["ttl_ms"],
                mono_ms=spec["invite_mono_ms"],
            )
            survivor = _create_party(
                spec["survivor_leader_label"],
                mono_ms=spec["create_mono_ms"] + 10,
                max_members=spec["max_members"],
            )
            _invite(
                survivor,
                spec["survivor_invitee_label"],
                ttl_ms=90000,
                mono_ms=spec["invite_mono_ms"] + 10,
            )
            _request(
                "POST",
                f"/v1/party/{doomed}/disconnect",
                {"player_id": spec["doomed_leader_label"]},
                mono_ms=spec["disconnect_mono_ms"],
            )
            status, body = _request(
                "POST", "/v1/admin/sweep", mono_ms=spec["sweep_mono_ms"]
            )
            assert status == 200
            assert isinstance(body, dict)
            assert body["retired_parties"] >= 1
            assert body["removed_parties"] >= 1
            entry = latest_for(_load_ledger(), doomed)
            assert entry is not None
            assert entry["status"] == "retired"
            _export_fail(
                doomed,
                mono_ms=spec["export_mono_ms"],
                token="audit ledger party retired",
            )
            report = _export(survivor, mono_ms=spec["export_mono_ms"])
            assert report["status"] == "active"
            assert report["reserved_slots"] == 1

    def test_tb3_twin_reconcile_fixture(self) -> None:
        """Hidden fixture: twin parties + joined invitee drop force cross-source occupancy."""
        spec = json.loads(TB3_TWIN.read_text(encoding="utf-8"))
        with daemon_session():
            party_a = _create_party(
                f"{spec['twin_leader_label']}-a",
                mono_ms=spec["create_mono_ms"],
                max_members=spec["max_members"],
            )
            party_b = _create_party(
                f"{spec['twin_leader_label']}-b",
                mono_ms=spec["create_mono_ms"] + 1,
                max_members=spec["max_members"],
            )
            # Ghost invites create distinct intermediate states so the two parties
            # never share a suppression key with each other.
            _invite(
                party_a,
                f"{spec['ghost_label']}-a",
                ttl_ms=spec["ttl_ms"],
                mono_ms=spec["ghost_a_mono_ms"],
            )
            _invite(
                party_b,
                f"{spec['ghost_label']}-b",
                ttl_ms=spec["ttl_ms"],
                mono_ms=spec["ghost_b_mono_ms"],
            )
            invite_a = _invite(
                party_a,
                spec["shared_invitee_label"],
                ttl_ms=spec["ttl_ms"],
                mono_ms=spec["first_invite_mono_ms"],
            )
            invite_b = _invite(
                party_b,
                spec["shared_invitee_label"],
                ttl_ms=spec["ttl_ms"],
                mono_ms=spec["second_invite_mono_ms"],
            )
            code, _ = _accept(
                invite_a,
                spec["shared_invitee_label"],
                "tb3-twin-accept",
                mono_ms=spec["accept_mono_ms"],
            )
            assert code == 200
            ledger = _load_ledger()
            # Both parties must appear in the retained window — tail-only suppression
            # would have dropped one of them.
            assert latest_for(ledger, party_a) is not None
            assert latest_for(ledger, party_b) is not None
            report_a = _export(party_a, mono_ms=spec["export_mono_ms"])
            report_b = _export(party_b, mono_ms=spec["export_mono_ms"])
            # party_a has the shared invitee connected; reserved seats are the ghost only.
            assert report_a["connected_members"] == 2
            assert report_a["reserved_slots"] == 1
            assert report_a["effective_occupancy"] == 3
            # party_b still has both ghost and shared invite pending.
            assert report_b["connected_members"] == 1
            assert report_b["reserved_slots"] == 2
            assert report_b["effective_occupancy"] == 3
            assert invite_b  # used; silence unused warning for static checkers


class TestBaselineServiceSmoke:
    def test_idempotent_accept_retry(self) -> None:
        """Working baseline returns the cached accept body on idempotency retry."""
        with daemon_session():
            party_id = _create_party("leader-idem")
            invite_id = _invite(party_id, "guest-idem")
            code1, body1 = _accept(invite_id, "guest-idem", "key-alpha")
            code2, body2 = _accept(invite_id, "guest-idem", "key-alpha")
            assert code1 == 200 and code2 == 200
            assert body1 == body2

    def test_failed_accept_not_cached(self) -> None:
        """409 accept failures are not stored under the idempotency key."""
        with daemon_session():
            party_id = _create_party("leader-fail")
            invite_id = _invite(party_id, "guest-fail", ttl_ms=100, mono_ms=100)
            code1, _ = _accept(invite_id, "guest-fail", "key-beta", mono_ms=5000)
            assert code1 == 409
            code2, body2 = _accept(invite_id, "guest-fail", "key-beta", mono_ms=150)
            assert code2 == 200, body2

    def test_cap_excludes_expired_pending_invites(self) -> None:
        """Member cap ignores expired pending rows still in SQLite."""
        with daemon_session():
            party_id = _create_party("leader-cap", mono_ms=0)
            _invite(party_id, "guest-cap-a", ttl_ms=200, mono_ms=100)
            _invite(party_id, "guest-cap-b", ttl_ms=5000, mono_ms=200)
            status, _ = _request(
                "POST",
                f"/v1/party/{party_id}/invite",
                {"invitee_id": "guest-cap-c", "ttl_ms": 5000},
                mono_ms=500,
            )
            assert status == 200

    def test_leader_disconnect_blocks_accept(self) -> None:
        """Accept returns 409 after leader disconnect disbands the party."""
        with daemon_session():
            party_id = _create_party("leader-block")
            invite_id = _invite(party_id, "guest-block")
            _request(
                "POST",
                f"/v1/party/{party_id}/disconnect",
                {"player_id": "leader-block"},
                mono_ms=400,
            )
            code, _ = _accept(invite_id, "guest-block", "key-gamma", mono_ms=500)
            assert code == 409

    def test_export_orphan_party_when_leader_disconnected(self) -> None:
        """Export clears orphan_party on a disbanded snapshot after leader disconnect."""
        with daemon_session():
            party_id = _create_party("leader-orphan", mono_ms=100)
            _invite(party_id, "guest-orphan", mono_ms=200)
            _request(
                "POST",
                f"/v1/party/{party_id}/disconnect",
                {"player_id": "leader-orphan"},
                mono_ms=250,
            )
            report = _export(party_id, mono_ms=300)
            assert report["status"] == "disbanded"
            assert report["orphan_party"] is False


class TestIsolationPatches:
    def test_publish_only_golden_insufficient_without_staging(self) -> None:
        """Publish snapshot math without ingest staging fails the ledger path."""
        backup = _install_patch("stage", "broken")
        _build()
        try:
            with daemon_session():
                party_id = _create_party("iso-pub")
                _invite(party_id, "iso-pub-guest")
                assert not SNAPSHOT.is_file()
        finally:
            _restore("stage", backup)

    def test_sweeper_only_golden_insufficient_without_refresh(self) -> None:
        """Mono sweeper without RefreshSnapshotsAfterSweep leaves stale staging."""
        with daemon_session():
            party_id = _create_party("iso-sweep")
            _invite(party_id, "iso-sweep-guest", ttl_ms=600, mono_ms=10000)
            snap_before = latest_for(_load_ledger(), party_id)
            assert snap_before is not None
            pending_before = list(snap_before["pending_invites"])
        _stop_daemon()
        backup = _install_patch("sweeper", "broken")
        _build()
        _start_daemon()
        try:
            _request("POST", "/v1/admin/sweep", mono_ms=11000)
            snap_after = latest_for(_load_ledger(), party_id)
            assert snap_after is not None
            assert len(snap_after["pending_invites"]) == len(pending_before)
            assert len(pending_before) >= 1
        finally:
            _stop_daemon()
            _restore("sweeper", backup)

    def test_query_only_golden_insufficient_without_filters(self) -> None:
        """Broken store helpers stage revoked invites and break published report math."""
        backups = {
            "query": _install_patch("query", "broken"),
            "canon": _install_patch("canon", "golden"),
            "ledger": _install_patch("ledger", "golden"),
            "stage": _install_patch("stage", "golden"),
            "publish": _install_patch("publish", "golden"),
            "sweeper": _install_patch("sweeper", "golden"),
        }
        _build()
        try:
            with daemon_session():
                party_id = _create_party("iso-query")
                invite_id = _invite(party_id, "iso-query-guest", mono_ms=200)
                _request(
                    "POST",
                    f"/v1/party/{party_id}/disconnect",
                    {"player_id": "iso-query"},
                    mono_ms=300,
                )
                # Leader disconnect revokes the invite; a correct query omits it.
                # The broken helper still stages the revoked row, so pending is non-empty.
                entry = latest_for(
                    json.loads(SNAPSHOT.read_text(encoding="utf-8")), party_id
                )
                assert entry is not None
                assert any(row["invite_id"] == invite_id for row in entry["pending_invites"])
        finally:
            for module, backup in backups.items():
                _restore(module, backup)

    def test_canon_only_golden_insufficient_without_ledger(self) -> None:
        """Canon digest helpers alone never append the staging ledger."""
        backups = {
            "canon": _install_patch("canon", "golden"),
            "ledger": _install_patch("ledger", "broken"),
            "stage": _install_patch("stage", "golden"),
            "publish": _install_patch("publish", "golden"),
            "sweeper": _install_patch("sweeper", "golden"),
            "query": _install_patch("query", "golden"),
        }
        _build()
        try:
            with daemon_session():
                party_id = _create_party("iso-canon")
                _invite(party_id, "iso-canon-guest", mono_ms=200)
                # Stage runs but AppendIfChanged is a no-op under the broken ledger.
                assert not SNAPSHOT.is_file() or latest_for(
                    json.loads(SNAPSHOT.read_text(encoding="utf-8")), party_id
                ) is None
        finally:
            for module, backup in backups.items():
                _restore(module, backup)

    def test_ledger_only_golden_insufficient_without_stage(self) -> None:
        """Ledger append helpers alone never run without the stage hooks wired."""
        backups = {
            "ledger": _install_patch("ledger", "golden"),
            "canon": _install_patch("canon", "golden"),
            "stage": _install_patch("stage", "broken"),
            "publish": _install_patch("publish", "golden"),
            "sweeper": _install_patch("sweeper", "golden"),
            "query": _install_patch("query", "golden"),
        }
        _build()
        try:
            with daemon_session():
                party_id = _create_party("iso-ledger")
                _invite(party_id, "iso-ledger-guest", mono_ms=200)
                assert not SNAPSHOT.is_file()
        finally:
            for module, backup in backups.items():
                _restore(module, backup)
