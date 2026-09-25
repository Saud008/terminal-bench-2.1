"""Livattest attestation gate behavioral verifier."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from reference_livattest_chain import (
    derive_session_id,
    derive_token,
    scenario_discontinuity_span,
    scenario_grace_expired_ban,
    scenario_ticket_rebind,
    scenario_uint32_wrap_edge,
    seed_mix,
)
from livattest_harness import (
    APP,
    DB,
    EXTRA_SEEDS,
    PROTECTED_SHA256,
    REPORT,
    SEED,
    SNAPSHOT,
    attest_batch,
    attest_export,
    load_protected,
    oracle_slices,
    run_discontinuity_batches,
    runtime_session,
    seeded_runtime,
    sha256_file,
    start_daemon,
    trust_bind,
)

load_protected({
    "cmd/livattest/main.go": "81dc9bdc570db21b83522c43ea3e9495d844903959a38fb875eb6ff3a5c1c6dc",
    "config/livattest.json": "1dda9a45dad8eb4bfbe9daa2e1e576e1ea23b77e95a3f17681a2cc0b08caf71c",
    "docs/admission-ticket.md": "39e69255966166e9807f96c56df44ab8bf647662a7905172a668c7ecaefbb2cf",
    "docs/attest-export.md": "7cfe79f1e9717fd24b77b9a646160bbd9b5d3ee687985b07ed58502bad1a370e",
    "docs/attest-report-format.md": "e9accb3ef2e5f361eee983a3230d25512f678f074e6c1d0f5d6880c7b98adc7a",
    "docs/breach-seal.md": "2d72fcac30787e91e71332f9507990ae9050dfd68cd702a90c01f64c4836f4b4",
    "docs/continuity-policy.md": "e70bd278c79afa54fac903c3d7da7f07c39092feaffd8a61cd48a7cd33683b5e",
    "docs/fixture-catalog.md": "d82a0d1a60e7924c6b257966ccf5a9ac879a50ae3b848d9c5eb046a9a08c784a",
    "docs/trust-surface.md": "4a3d50f08d5e66a4b8f91b14bb78811bf36076cd78835eaae940b069be37f08f",
    "docs/witness-chain.md": "56dc9735ad3b03857fdfbe168d28a9f997b21a5056a53275b8607223e5b7a0e1",
    "fixtures/catalog.json": "6c29795a4d333bf81e474ede05b0266e4a1d037d807ac1390a5c526d51eaef66",
    "internal/api/server.go": "f23e3179d84ddb77fce5ebd87e460688845586fba3774134223f9985edafa1a4",
})


class TestTrustSurfaceIntegrity:
    def test_t3a242c_trust_surface_hashes_immutable(self) -> None:
        """Verifier hash-checks protected docs, config, and API wiring."""
        for rel, expected in PROTECTED_SHA256.items():
            assert sha256_file(APP / rel) == expected, rel


class TestHmacContinuityPolicy:
    def test_t3a242c_discontinuity_span_matches_chain_refmath(self) -> None:
        """Breach seal span closure and digest-sealed export match refmath witness."""
        ref = scenario_discontinuity_span(SEED)
        with runtime_session():
            run_discontinuity_batches(ref)
            report = attest_export(ref.token, ref.session_id)
        expected = ref.export()
        for key in (
            "last_seq",
            "breaches_opened",
            "breaches_closed",
            "missing_span_total",
            "active_ban_seals",
            "repair_events",
            "witness_seq",
            "witness_head",
            "audit_digest",
        ):
            assert report[key] == expected[key], key

    def test_t3a242c_uint32_wrap_edge_no_breach_seal(self) -> None:
        """MaxUint32 rollover admits without minting a discontinuity breach seal."""
        ref = scenario_uint32_wrap_edge(SEED)
        with runtime_session():
            ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
            base = ref.anchor_client
            for seq, delta, mono in (
                (4294967294, 0, 100),
                (4294967295, 100, 200),
                (0, 200, 300),
                (1, 300, 400),
            ):
                attest_batch(
                    ref.token,
                    ref.session_id,
                    ticket,
                    [{"seq": seq, "client_ms": base + delta}],
                    mono,
                )
            report = attest_export(ref.token, ref.session_id)
        assert report["breaches_opened"] == 0
        assert report["last_seq"] == 1

    def test_t3a242c_ticket_rebind_scopes_duplicate_policy(self) -> None:
        """HMAC ticket rebind gives the new session an independent seq namespace."""
        old_ref, new_ref = scenario_ticket_rebind(SEED)
        with runtime_session():
            ticket_old = trust_bind(old_ref.token, old_ref.session_id, old_ref.anchor_client, mono_ms=0)
            attest_batch(
                old_ref.token,
                old_ref.session_id,
                ticket_old,
                [
                    {"seq": 10, "client_ms": old_ref.anchor_client},
                    {"seq": 11, "client_ms": old_ref.anchor_client + 200},
                ],
                200,
            )
            ticket_new = trust_bind(new_ref.token, new_ref.session_id, new_ref.anchor_client, mono_ms=300)
            status = attest_batch(
                new_ref.token,
                new_ref.session_id,
                ticket_new,
                [{"seq": 10, "client_ms": new_ref.anchor_client}],
                400,
                expect_ok=False,
            )
            assert status == 200
            attest_batch(
                new_ref.token,
                new_ref.session_id,
                ticket_new,
                [{"seq": 11, "client_ms": new_ref.anchor_client + 200}],
                450,
            )
            report = attest_export(new_ref.token, new_ref.session_id)
        assert report["duplicate_rejections"] == 0

    def test_t3a242c_anchor_skew_policy_returns_409(self) -> None:
        """Skew tolerance policy rejects beats outside the anchored envelope."""
        token = derive_token("player", SEED, "skew")
        session = derive_session_id("sess-skew", SEED, "skew")
        base_ms = 30000 + (seed_mix(SEED, "skew:ms") % 250)
        with runtime_session():
            ticket = trust_bind(token, session, base_ms, mono_ms=0)
            attest_batch(token, session, ticket, [{"seq": 1, "client_ms": base_ms}], 0)
            attest_batch(token, session, ticket, [{"seq": 2, "client_ms": base_ms + 500}], 600)
            status = attest_batch(
                token,
                session,
                ticket,
                [{"seq": 3, "client_ms": base_ms + 5000}],
                600,
                expect_ok=False,
            )
            assert status == 409
            report = attest_export(token, session)
        assert report["skew_rejections"] == 1

    def test_t3a242c_grace_expired_ban_seal_persists(self) -> None:
        """Ban seal stays active when span closure happens outside the grace window."""
        ref = scenario_grace_expired_ban(SEED)
        with runtime_session():
            ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
            base = ref.anchor_client
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 1, "client_ms": base}], 100)
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 5, "client_ms": base + 7000}], 7000)
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 2, "client_ms": base + 12001}], 12001)
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 3, "client_ms": base + 12100}], 12100)
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 4, "client_ms": base + 12200}], 12200)
            report = attest_export(ref.token, ref.session_id)
        expected = ref.export()
        assert report["active_ban_seals"] == expected["active_ban_seals"] == 1
        assert report["breaches_closed"] == 1


@pytest.mark.parametrize("extra_seed", EXTRA_SEEDS)
def test_t3a242c_seed_matrix_attest_digest(extra_seed: str) -> None:
    """Mutated identities per seed block static attest JSON shortcuts."""
    ref = scenario_discontinuity_span(extra_seed)
    with seeded_runtime(extra_seed):
        run_discontinuity_batches(ref)
        report = attest_export(ref.token, ref.session_id)
    assert report == ref.export()


def test_t3a242c_unbound_attest_ticket_returns_400() -> None:
    """Attest batch without trust bind is rejected by the admission gate."""
    token = derive_token("player", SEED, "nobind")
    session = derive_session_id("sess-nobind", SEED, "nobind")
    with runtime_session():
        status = attest_batch(
            token,
            session,
            "deadbeef",
            [{"seq": 1, "client_ms": 1000}],
            0,
            expect_ok=False,
        )
    assert status == 400


def test_t3a242c_duplicate_seq_ticket_returns_409() -> None:
    """Continuity policy rejects duplicate accepted sequence tickets."""
    token = derive_token("player", SEED, "dup")
    session = derive_session_id("sess-dup", SEED, "dup")
    base = 12000 + (seed_mix(SEED, "dup:ms") % 100)
    with runtime_session():
        ticket = trust_bind(token, session, base, mono_ms=0)
        attest_batch(token, session, ticket, [{"seq": 5, "client_ms": base}], 100)
        status = attest_batch(
            token,
            session,
            ticket,
            [{"seq": 5, "client_ms": base + 10}],
            200,
            expect_ok=False,
        )
        assert status == 409
        report = attest_export(token, session)
    assert report["duplicate_rejections"] == 1


def test_t3a242c_instruction_attest_output_paths_materialize() -> None:
    """Attest export and witness snapshot paths from instruction are written on success."""
    ref = scenario_discontinuity_span(SEED)
    with runtime_session():
        run_discontinuity_batches(ref)
        report = attest_export(ref.token, ref.session_id)
    assert str(REPORT) == "/app/output/attest-report.json"
    assert str(SNAPSHOT) == "/app/state/witness-snapshot.json"
    assert REPORT.is_file()
    assert SNAPSHOT.is_file()
    assert report["token"] == ref.token


class TestWitnessChainStaging:
    def test_t3a242c_witness_file_materializes_after_admit(self) -> None:
        """Successful admit batch writes witness-snapshot.json per witness-chain contract."""
        ref = scenario_discontinuity_span(SEED)
        with runtime_session():
            run_discontinuity_batches(ref)
            assert SNAPSHOT.is_file()
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["version"] == 1
        assert snap["token"] == ref.token

    def test_t3a242c_witness_head_chain_advances_seq(self) -> None:
        """witness_seq increments monotonically across staged witness heads."""
        ref = scenario_discontinuity_span(SEED)
        with runtime_session():
            ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
            base = ref.anchor_client
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 1, "client_ms": base}], 100)
            first = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["witness_seq"]
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": 2, "client_ms": base + 50}], 200)
            second = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["witness_seq"]
        assert second == first + 1


class TestDigestSealedExport:
    def test_t3a242c_live_skew_counter_not_from_witness_file(self) -> None:
        """Digest export merges live session skew counter, ignoring tampered witness file."""
        from reference_livattest_chain import derive_session_id, derive_token, seed_mix

        token = derive_token("player", SEED, "rej-live")
        session = derive_session_id("sess-rej-live", SEED, "rej-live")
        base_ms = 31000 + (seed_mix(SEED, "rej-live:ms") % 100)
        with runtime_session():
            ticket = trust_bind(token, session, base_ms, mono_ms=0)
            attest_batch(token, session, ticket, [{"seq": 1, "client_ms": base_ms}], 0)
            attest_batch(token, session, ticket, [{"seq": 2, "client_ms": base_ms + 500}], 600)
            status = attest_batch(
                token,
                session,
                ticket,
                [{"seq": 3, "client_ms": base_ms + 5000}],
                600,
                expect_ok=False,
            )
            assert status == 409
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            snap["skew_rejections"] = 0
            SNAPSHOT.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
            report = attest_export(token, session)
        assert report["skew_rejections"] == 1

    def test_t3a242c_seal_counters_bind_to_witness_not_sqlite(self) -> None:
        """Attest seal reads breach counters from witness snapshot, not SQLite counters."""
        ref = scenario_discontinuity_span(SEED)
        with runtime_session():
            run_discontinuity_batches(ref)
            baseline = attest_export(ref.token, ref.session_id)
            conn = sqlite3.connect(DB)
            try:
                conn.execute(
                    "UPDATE counters SET breaches_closed = breaches_closed + 50 WHERE token=? AND session_id=?",
                    (ref.token, ref.session_id),
                )
                conn.commit()
            finally:
                conn.close()
            report = attest_export(ref.token, ref.session_id)
        assert report["breaches_closed"] == baseline["breaches_closed"]

    def test_t3a242c_sqlite_witness_survives_process_restart(self) -> None:
        """SQLite journal preserves attest digest across livattest process restart."""
        ref = scenario_discontinuity_span(SEED)
        with runtime_session():
            run_discontinuity_batches(ref)
            first = attest_export(ref.token, ref.session_id)
            subprocess.run(["pkill", "-9", "-x", "livattest"], check=False)
            start_daemon()
            second = attest_export(ref.token, ref.session_id)
        assert second == first


class TestOracleSliceTraps:
    def test_t3a242c_digest_without_witness_file_fails(self) -> None:
        """Digest publisher alone cannot attest without a staged witness file."""
        ref = scenario_discontinuity_span(SEED)
        with oracle_slices("emit"):
            with runtime_session():
                ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
                attest_batch(ref.token, ref.session_id, ticket, [{"seq": 1, "client_ms": ref.anchor_client}], 100)
                assert not SNAPSHOT.is_file()

    def test_t3a242c_witness_without_policy_rejects_span_closure(self) -> None:
        """Witness staging alone cannot admit span-closure beats rejected as duplicate."""
        ref = scenario_discontinuity_span(SEED)
        with oracle_slices("chain"):
            with runtime_session():
                ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
                base = ref.anchor_client
                attest_batch(ref.token, ref.session_id, ticket, [{"seq": 1, "client_ms": base}], 500)
                attest_batch(ref.token, ref.session_id, ticket, [{"seq": 4, "client_ms": base + 1200}], 1500)
                status = attest_batch(
                    ref.token,
                    ref.session_id,
                    ticket,
                    [{"seq": 2, "client_ms": base + 400}],
                    2000,
                    expect_ok=False,
                )
                assert status == 409

    def test_t3a242c_policy_witness_without_digest_rewalks_sqlite(self) -> None:
        """Policy+witness without digest publisher rewalks corrupted SQLite counters."""
        ref = scenario_discontinuity_span(SEED)
        with oracle_slices("continuity", "trust", "ban", "chain", "pin"):
            with runtime_session():
                run_discontinuity_batches(ref)
                baseline = attest_export(ref.token, ref.session_id)
                conn = sqlite3.connect(DB)
                try:
                    conn.execute(
                        "UPDATE counters SET breaches_closed = breaches_closed + 50 WHERE token=? AND session_id=?",
                        (ref.token, ref.session_id),
                    )
                    conn.commit()
                finally:
                    conn.close()
                report = attest_export(ref.token, ref.session_id)
            assert report["breaches_closed"] != baseline["breaches_closed"]


def test_t3a242c_hidden_linear_chain_refmath() -> None:
    """Hidden fixture seed validates discontinuity span refmath on unseen identities."""
    spec = json.loads(Path("/opt/verifier-fixtures/attest_hidden_linear.json").read_text(encoding="utf-8"))
    seed = spec["verifier_seed"]
    ref = scenario_discontinuity_span(seed)
    with seeded_runtime(seed):
        run_discontinuity_batches(ref)
        report = attest_export(ref.token, ref.session_id)
    assert report == ref.export()
    assert report["breaches_closed"] == spec["expected_breaches_closed"]


def test_t3a242c_hidden_wrap_chain_refmath() -> None:
    """Hidden fixture seed validates uint32 wrap edge without breach seal."""
    spec = json.loads(Path("/opt/verifier-fixtures/attest_hidden_wrap.json").read_text(encoding="utf-8"))
    seed = spec["verifier_seed"]
    ref = scenario_uint32_wrap_edge(seed)
    with seeded_runtime(seed):
        ticket = trust_bind(ref.token, ref.session_id, ref.anchor_client, mono_ms=0)
        base = ref.anchor_client
        for seq, delta, mono in (
            (4294967294, 0, 100),
            (4294967295, 100, 200),
            (0, 200, 300),
            (1, 300, 400),
        ):
            attest_batch(ref.token, ref.session_id, ticket, [{"seq": seq, "client_ms": base + delta}], mono)
        report = attest_export(ref.token, ref.session_id)
    assert report["last_seq"] == spec["expected_last_seq"]
    assert report["breaches_opened"] == spec["expected_breaches_opened"]
