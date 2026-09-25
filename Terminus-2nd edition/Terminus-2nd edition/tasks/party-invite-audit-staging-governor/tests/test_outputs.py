"""Behavioral verifier for the host-local party occupancy operations desk."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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
BIN = APP / "bin/partyd"
SNAPSHOT = APP / "state/party-audit-snapshot.json"
EXPORT = APP / "output/party-audit.json"
RESET = APP / "scripts/reset-state.sh"
PATCHES = Path(__file__).parent / "patches"
MANIFEST = Path("/opt/verifier-fixtures/protected-manifest.json")
FIXTURES = {
    name: Path("/opt/verifier-fixtures") / name
    for name in (
        "tb3_retention_chain.json",
        "tb3_sweep_retire.json",
        "tb3_twin_reconcile.json",
        "tb3_leader_disconnect.json",
    )
}
PATCH_TARGETS = {
    name: APP / "lib/party" / f"{name}.py"
    for name in ("canon", "ledger", "stage", "publish", "sweeper", "query")
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
    "lib/party/lifecycle.py",
    "lib/party/cli.py",
    "lib/party/db.py",
    "lib/party/schema.py",
    "lib/party/config.py",
    "lib/party/clock.py",
    "lib/party/decoy.py",
    "lib/party/__init__.py",
    "scripts/partyd",
]


def run(*argv: str) -> tuple[int, dict | str]:
    proc = subprocess.run(
        [str(BIN), *argv], cwd=APP, text=True, capture_output=True, check=False
    )
    raw = (proc.stdout if proc.returncode == 0 else proc.stderr).strip()
    try:
        return proc.returncode, json.loads(raw)
    except json.JSONDecodeError:
        return proc.returncode, raw


def rebuild() -> None:
    subprocess.run(["bash", "/app/scripts/verifier-rebuild.sh"], check=True)


def reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


@contextmanager
def ops_session():
    reset()
    rebuild()
    yield


def create(leader: str, mono=100, maximum=4) -> str:
    code, body = run(
        "create",
        "--leader",
        leader,
        "--max-members",
        str(maximum),
        "--mono-ms",
        str(mono),
    )
    assert code == 0, body
    return body["party_id"]


def invite(party: str, invitee: str, ttl=5000, mono=200) -> str:
    code, body = run(
        "invite",
        "--party",
        party,
        "--invitee",
        invitee,
        "--ttl-ms",
        str(ttl),
        "--mono-ms",
        str(mono),
    )
    assert code == 0, body
    return body["invite_id"]


def accept(invite_id: str, invitee: str, key: str, mono=300):
    return run(
        "accept",
        "--invite",
        invite_id,
        "--invitee",
        invitee,
        "--idempotency-key",
        key,
        "--mono-ms",
        str(mono),
    )


def sweep(mono: int):
    return run("sweep", "--mono-ms", str(mono))


def export(party: str, mono: int) -> dict:
    code, body = run("export", "--party", party, "--mono-ms", str(mono))
    assert code == 0, body
    return json.loads(EXPORT.read_text())


def export_fails(party: str, mono: int, token: str) -> None:
    before = EXPORT.read_bytes() if EXPORT.exists() else None
    code, body = run("export", "--party", party, "--mono-ms", str(mono))
    assert code == 3 and body == token
    assert (EXPORT.read_bytes() if EXPORT.exists() else None) == before


def ledger() -> dict:
    value = json.loads(SNAPSHOT.read_text())
    verify_ledger(value)
    return value


def test_protected_files_unchanged():
    manifest = json.loads(MANIFEST.read_text())
    for rel in PROTECTED:
        assert rel in manifest and (APP / rel).is_file()
        assert hashlib.sha256((APP / rel).read_bytes()).hexdigest() == manifest[rel]


def test_instruction_output_paths_exist():
    with ops_session():
        party = create("leader")
        inv = invite(party, "guest")
        assert accept(inv, "guest", "id")[0] == 0
        report = export(party, 400)
        assert SNAPSHOT.is_file() and EXPORT.is_file() and report["party_id"] == party


class TestStagingIngest:
    def test_invite_appends_ledger_entry(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest", mono=500)
            entry = latest_for(ledger(), party)
            assert (
                entry["status"] == "active"
                and entry["pending_invites"][0]["invitee_id"] == "guest"
            )

    def test_accept_increments_party_seq(self):
        with ops_session():
            party = create("leader")
            inv = invite(party, "guest")
            first = latest_for(ledger(), party)["party_seq"]
            assert accept(inv, "guest", "key", 300)[0] == 0
            assert latest_for(ledger(), party)["party_seq"] == first + 1

    def test_leader_disconnect_stages_disbanded_snapshot(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest")
            assert (
                run(
                    "disconnect",
                    "--party",
                    party,
                    "--player",
                    "leader",
                    "--mono-ms",
                    "300",
                )[0]
                == 0
            )
            entry = latest_for(ledger(), party)
            assert (
                entry["status"] == "disbanded"
                and not entry["connected_ids"]
                and not entry["pending_invites"]
            )

    def test_suppression_keeps_digests_identical_on_noop_sweep(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest", ttl=90000, mono=1000)
            before = ledger()
            assert sweep(1100)[0] == 0
            after = ledger()
            assert after["sweep_epoch"] == 1 and [
                x["entry_digest"] for x in before["entries"]
            ] == [x["entry_digest"] for x in after["entries"]]


class TestCanonicalDigest:
    def test_worked_vector_matches_docs(self):
        line = entry_line(
            1,
            "pty_demo",
            1,
            200,
            0,
            "active",
            "leader-a",
            4,
            ["leader-a"],
            [{"invite_id": "inv_a1", "invitee_id": "guest-a", "expires_mono_ms": 5200}],
        )
        assert (
            digest(GENESIS, line)
            == "b76a731bc3b2c737a7da6be696adf23c8d4329b7daec03eb3215d8803faff2f7"
        )

    def test_pending_sort_is_expiry_then_id(self):
        with ops_session():
            party = create("leader")
            first = invite(party, "z", 2000, 200)
            second = invite(party, "a", 9000, 300)
            assert [
                x["invite_id"] for x in latest_for(ledger(), party)["pending_invites"]
            ] == [first, second]


class TestExportPublish:
    def test_effective_occupancy_from_staged_pending(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest", 8000, 1000)
            entry = latest_for(ledger(), party)
            report = export(party, 2000)
            assert report["effective_occupancy"] == effective_occupancy(
                report["connected_members"],
                entry["pending_invites"],
                entry["connected_ids"],
                2000,
            )

    def test_live_sqlite_pending_counts_after_sweep(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest", 1000, 3000)
            assert export(party, 3500)["pending_invites"] == 1
            sweep(5000)
            report = export(party, 5000)
            assert report["pending_invites"] == report["reserved_slots"] == 0

    def test_reserved_dedupe_and_joined_drop(self):
        with ops_session():
            party = create("leader", maximum=6)
            first = invite(party, "same", 20000, 200)
            invite(party, "other", 20000, 300)
            assert export(party, 400)["reserved_slots"] == 2
            assert accept(first, "same", "join", 500)[0] == 0
            assert export(party, 600)["reserved_slots"] == 1

    def test_refuses_missing_broken_and_drift(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest")
            SNAPSHOT.unlink()
            export_fails(party, 300, "audit ledger unavailable")
        with ops_session():
            party = create("leader")
            invite(party, "guest")
            value = ledger()
            value["entries"][-1]["entry_digest"] = "f" * 64
            SNAPSHOT.write_text(json.dumps(value))
            export_fails(party, 300, "audit ledger chain broken")
        with ops_session():
            party = create("leader")
            invite(party, "guest")
            value = ledger()
            entry = value["entries"][-1]
            entry["max_members"] = 99
            entry["entry_digest"] = digest(
                entry["prev_digest"],
                entry_line(
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
                ),
            )
            value["chain_head"] = entry["entry_digest"]
            SNAPSHOT.write_text(json.dumps(value))
            export_fails(party, 300, "audit ledger drift")


class TestSweepRefresh:
    def test_monotonic_expire_refresh_and_epoch_across_processes(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest", 500, 7000)
            assert sweep(7600)[1]["expired_invites"] == 1
            assert latest_for(ledger(), party)["pending_invites"] == []
            assert sweep(7700)[1]["sweep_epoch"] == 2

    def test_tb3_leader_disconnect_export_fixture(self):
        spec = json.loads(FIXTURES["tb3_leader_disconnect.json"].read_text())
        with ops_session():
            party = create(spec["leader_label"], 1000)
            invite(party, spec["invitee_label"], mono=1200)
            run(
                "disconnect",
                "--party",
                party,
                "--player",
                spec["leader_label"],
                "--mono-ms",
                str(spec["disconnect_mono_ms"]),
            )
            assert export(party, spec["export_mono_ms"])["status"] == "disbanded"

    def test_tb3_retention_chain_fixture(self):
        spec = json.loads(FIXTURES["tb3_retention_chain.json"].read_text())
        with ops_session():
            party = create(
                spec["leader_label"], spec["create_mono_ms"], spec["max_members"]
            )
            ids = [
                invite(
                    party,
                    f"{spec['invitee_prefix']}-{i}",
                    spec["ttl_ms"],
                    spec["invite_mono_ms"] + i,
                )
                for i in range(spec["invite_count"])
            ]
            for i in range(spec["accept_count"]):
                assert (
                    accept(
                        ids[i],
                        f"{spec['invitee_prefix']}-{i}",
                        f"k{i}",
                        spec["accept_mono_ms"] + i,
                    )[0]
                    == 0
                )
            value = ledger()
            assert len(value["entries"]) == RETAINED and value["chain_base"] != GENESIS

    def test_tb3_sweep_retire_fixture(self):
        spec = json.loads(FIXTURES["tb3_sweep_retire.json"].read_text())
        with ops_session():
            doomed = create(
                spec["doomed_leader_label"], spec["create_mono_ms"], spec["max_members"]
            )
            invite(
                doomed,
                spec["doomed_invitee_label"],
                spec["ttl_ms"],
                spec["invite_mono_ms"],
            )
            survivor = create(
                spec["survivor_leader_label"],
                spec["create_mono_ms"] + 10,
                spec["max_members"],
            )
            invite(
                survivor,
                spec["survivor_invitee_label"],
                90000,
                spec["invite_mono_ms"] + 10,
            )
            run(
                "disconnect",
                "--party",
                doomed,
                "--player",
                spec["doomed_leader_label"],
                "--mono-ms",
                str(spec["disconnect_mono_ms"]),
            )
            assert sweep(spec["sweep_mono_ms"])[1]["retired_parties"] >= 1
            export_fails(doomed, spec["export_mono_ms"], "audit ledger party retired")
            assert export(survivor, spec["export_mono_ms"])["status"] == "active"

    def test_tb3_twin_reconcile_fixture(self):
        spec = json.loads(FIXTURES["tb3_twin_reconcile.json"].read_text())
        with ops_session():
            a = create(
                f"{spec['twin_leader_label']}-a",
                spec["create_mono_ms"],
                spec["max_members"],
            )
            b = create(
                f"{spec['twin_leader_label']}-b",
                spec["create_mono_ms"] + 1,
                spec["max_members"],
            )
            invite(
                a, f"{spec['ghost_label']}-a", spec["ttl_ms"], spec["ghost_a_mono_ms"]
            )
            invite(
                b, f"{spec['ghost_label']}-b", spec["ttl_ms"], spec["ghost_b_mono_ms"]
            )
            ia = invite(
                a,
                spec["shared_invitee_label"],
                spec["ttl_ms"],
                spec["first_invite_mono_ms"],
            )
            invite(
                b,
                spec["shared_invitee_label"],
                spec["ttl_ms"],
                spec["second_invite_mono_ms"],
            )
            accept(ia, spec["shared_invitee_label"], "twin", spec["accept_mono_ms"])
            assert (
                export(a, spec["export_mono_ms"])["reserved_slots"] == 1
                and export(b, spec["export_mono_ms"])["reserved_slots"] == 2
            )


class TestBaselineServiceSmoke:
    def test_idempotent_accept_retry_and_failure_not_cached(self):
        with ops_session():
            party = create("leader")
            inv = invite(party, "guest")
            one = accept(inv, "guest", "same")
            two = accept(inv, "guest", "same")
            assert one == two and one[0] == 0
            expired = invite(party, "late", ttl=100, mono=100)
            assert accept(expired, "late", "bad", mono=5000)[0] == 2
            assert accept(expired, "late", "bad", mono=150)[0] == 0

    def test_cap_excludes_expired_and_disconnect_blocks_accept(self):
        with ops_session():
            party = create("leader", maximum=3)
            invite(party, "a", ttl=200, mono=100)
            invite(party, "b", ttl=5000, mono=200)
            # at mono=500 invite a is expired, so third invite still fits under cap 3
            assert invite(party, "c", ttl=5000, mono=500)
            other = create("other", mono=550)
            inv = invite(other, "guest", mono=560)
            assert (
                run(
                    "disconnect",
                    "--party",
                    other,
                    "--player",
                    "other",
                    "--mono-ms",
                    "600",
                )[0]
                == 0
            )
            assert accept(inv, "guest", "blocked", mono=700)[0] == 2

    def test_disbanded_export_not_orphan(self):
        with ops_session():
            party = create("leader")
            invite(party, "guest")
            run(
                "disconnect", "--party", party, "--player", "leader", "--mono-ms", "250"
            )
            assert export(party, 300)["orphan_party"] is False


class TestIsolationPatches:
    def test_patch_assets_cover_all_six_modules(self):
        for name in PATCH_TARGETS:
            assert (PATCHES / f"broken_{name}.py").is_file()
            assert (PATCHES / f"golden_{name}.py").is_file()

    def test_stage_golden_alone_insufficient_without_ledger(self):
        backups = {
            name: path.read_text(encoding="utf-8")
            for name, path in PATCH_TARGETS.items()
        }
        try:
            for name, path in PATCH_TARGETS.items():
                shutil.copy(PATCHES / f"broken_{name}.py", path)
            shutil.copy(PATCHES / "golden_stage.py", PATCH_TARGETS["stage"])
            rebuild()
            reset()
            party = create("leader")
            invite(party, "guest")
            # golden stage still depends on ledger.AppendIfChanged; broken ledger writes nothing
            assert not SNAPSHOT.exists() or not json.loads(
                SNAPSHOT.read_text(encoding="utf-8")
            ).get("entries")
        finally:
            for name, path in PATCH_TARGETS.items():
                path.write_text(backups[name], encoding="utf-8")
            rebuild()

    def test_publish_golden_alone_cannot_stage(self):
        backups = {
            name: path.read_text(encoding="utf-8")
            for name, path in PATCH_TARGETS.items()
        }
        try:
            for name, path in PATCH_TARGETS.items():
                shutil.copy(PATCHES / f"broken_{name}.py", path)
            shutil.copy(PATCHES / "golden_publish.py", PATCH_TARGETS["publish"])
            rebuild()
            reset()
            party = create("leader")
            invite(party, "guest")
            assert not SNAPSHOT.exists() or not json.loads(
                SNAPSHOT.read_text(encoding="utf-8")
            ).get("entries")
        finally:
            for name, path in PATCH_TARGETS.items():
                path.write_text(backups[name], encoding="utf-8")
            rebuild()

    def test_all_goldens_restore_export(self):
        backups = {
            name: path.read_text(encoding="utf-8")
            for name, path in PATCH_TARGETS.items()
        }
        try:
            for name, path in PATCH_TARGETS.items():
                shutil.copy(PATCHES / f"golden_{name}.py", path)
            rebuild()
            reset()
            party = create("leader")
            invite(party, "guest")
            report = export(party, 300)
            assert report["reserved_slots"] == 1 and report["party_id"] == party
        finally:
            for name, path in PATCH_TARGETS.items():
                path.write_text(backups[name], encoding="utf-8")
            rebuild()
