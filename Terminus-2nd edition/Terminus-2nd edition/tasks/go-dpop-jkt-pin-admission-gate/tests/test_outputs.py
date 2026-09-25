"""Jktadmit jkt-pin admission gate behavioral verifier."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_92ac16d5_go import (
    DENY_REASONS,
    build_proof,
    derive_jti,
    derive_principal,
    derive_session,
    generate_keypair,
    scenario_clean_check_stream,
    seed_mix,
    tamper_header,
    tamper_signature,
)
from gate_harness import (
    BIN_MIRROR,
    CHECK_HTU,
    CLI,
    EXTRA_SEEDS,
    LEDGER,
    OPEN_HTU,
    APP,
    PROTECTED_SHA256,
    SEED,
    SNAPSHOT,
    check_proof,
    commit,
    http_json,
    load_protected,
    open_session,
    runtime_session,
    seeded_runtime,
    sha256_file,
)

load_protected({
    "cmd/jktadmit/main.go": "0bb695018b31534a7cf3ff92ef0f460cd1a9b9787dcf710a0847b276d0db90d9",
    "internal/gateway/routes.go": "d7484245c2e7f1ce53dc7dc62630338390f8343bc85d3130224fdae1b304e509",
    "config/jktadmit.json": "f928a211129856909333c22511ad6bacea6b15147e59bf4c3fa660d035dd4115",
    "docs/deny-ledger-seal.md": "14245e6c621777166253597af891b8d2adf2e8c457980966ab5b2c72f66d7f3a",
    "docs/vault-hmac-bind.md": "db4f27851910476c1fb44794992fe68fe5383fc78177d4edacf13b5a2c144cbc",
    "docs/jkt-thumbprint-policy.md": "0ae8723a2afa64a3f3ad2ab36faad94fadf3d373c1ea21a31cd27c1a0747ecb6",
    "docs/jti-nonce-window.md": "427e1e1f6e38de17ccbfa615ea097a489c8ea277da6ea5fdcc6f46516cf586de",
    "docs/dpop-http-routes.md": "79aa7fa90a24c4f8cb3b2707b1fb949b1d55eb82362b3a0e575260b457f21bca",
    "fixtures/sample_dpop_proofs.json": "967bcc3365051eb7e1a97adf54e7772409b4517cec0ac1b0fb9f7e88d5b1b0e8",
})


class TestGateSurfaceIntegrity:
    def test_t92ac16_jka77f3_protected_files_hash_locked(self) -> None:
        """Verifier hash-checks protected docs, config, fixtures, and HTTP wiring."""
        for rel, expected in PROTECTED_SHA256.items():
            assert sha256_file(APP / rel) == expected, rel


class TestBinaryWiring:
    def test_t92ac16_jka77f3_binary_present_at_both_locations(self) -> None:
        """jktadmit is installed at both the canonical and /app/bin mirror paths."""
        assert CLI.is_file()
        assert BIN_MIRROR.is_file()

    def test_t92ac16_jka77f3_binary_usage_message_missing_subcommand(self) -> None:
        """Running the compiled binary with no subcommand exits 2 and prints a
        usage line, exercised via a direct subprocess call rather than the
        HTTP harness."""
        proc = subprocess.run([str(CLI)], capture_output=True, text=True, timeout=5)
        assert proc.returncode == 2
        assert "usage" in proc.stderr.lower()


class TestJKTThumbprint:
    def test_t92ac16_jka77f3_open_jkt_equals_sha256_thumbprint(self) -> None:
        """Open's returned jkt must equal the RFC 7638-style SHA-256 thumbprint,
        not a shorter SHA-1 digest."""
        kp = generate_keypair(f"jkt-check:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "jkt-check")
        session = derive_session(SEED, "jkt-check")
        now = 1_800_100_000 + (seed_mix(SEED, "jkt-check:iat") % 500)
        proof = build_proof(kp, derive_jti(SEED, "jkt-check", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, body = open_session(principal, session, proof, now_unix=now)
        assert body["jkt"] == kp.jkt()
        assert len(body["jkt"]) == 64

    def test_t92ac16_jka77f3_check_jkt_mismatch_denied_for_different_key(self) -> None:
        """A proof signed by a different keypair than the one pinned at open
        must be denied jkt_mismatch when it ingests through /gate/proof/check."""
        pinned_kp = generate_keypair(f"jkt-pin:{SEED}".encode("utf-8"))
        other_kp = generate_keypair(f"jkt-other:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "jkt-mismatch")
        session = derive_session(SEED, "jkt-mismatch")
        now = 1_800_110_000
        open_proof = build_proof(pinned_kp, derive_jti(SEED, "jkt-mismatch", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            check_proof_str = build_proof(other_kp, derive_jti(SEED, "jkt-mismatch", 1), "POST", CHECK_HTU, now)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 409
        assert body["reason"] == "jkt_mismatch"


class TestHTMPolicy:
    def test_t92ac16_jka77f3_htm_case_insensitive_admits(self) -> None:
        """A lower-case htm claim ("post") must still admit against the POST
        route, per the case-insensitive comparison in jkt-thumbprint-policy.md."""
        kp = generate_keypair(f"htm-case:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "htm-case")
        session = derive_session(SEED, "htm-case")
        now = 1_800_120_000
        open_proof = build_proof(kp, derive_jti(SEED, "htm-case", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            check_proof_str = build_proof(kp, derive_jti(SEED, "htm-case", 1), "post", CHECK_HTU, now)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 200, body
        assert body["verdict"] == "admit"

    def test_t92ac16_jka77f3_htm_wrong_method_denied(self) -> None:
        """A genuinely different HTTP method claim is denied htm_mismatch."""
        kp = generate_keypair(f"htm-wrong:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "htm-wrong")
        session = derive_session(SEED, "htm-wrong")
        now = 1_800_130_000
        open_proof = build_proof(kp, derive_jti(SEED, "htm-wrong", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            check_proof_str = build_proof(kp, derive_jti(SEED, "htm-wrong", 1), "GET", CHECK_HTU, now)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 409
        assert body["reason"] == "htm_mismatch"


class TestHTUPolicy:
    def test_t92ac16_jka77f3_htu_mismatch_denied(self) -> None:
        """A proof claiming the wrong canonical URL is denied htu_mismatch."""
        kp = generate_keypair(f"htu-wrong:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "htu-wrong")
        session = derive_session(SEED, "htu-wrong")
        now = 1_800_140_000
        open_proof = build_proof(kp, derive_jti(SEED, "htu-wrong", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            check_proof_str = build_proof(kp, derive_jti(SEED, "htu-wrong", 1), "POST", "https://evil.example/gate/proof/check", now)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 409
        assert body["reason"] == "htu_mismatch"


class TestIatSkewPolicy:
    def test_t92ac16_jka77f3_iat_future_skew_denied(self) -> None:
        """A proof timestamped far in the future must be denied iat_skew —
        the skew bound is symmetric, not past-only."""
        kp = generate_keypair(f"iat-future:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "iat-future")
        session = derive_session(SEED, "iat-future")
        now = 1_800_150_000
        open_proof = build_proof(kp, derive_jti(SEED, "iat-future", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            future_iat = now + 900
            check_proof_str = build_proof(kp, derive_jti(SEED, "iat-future", 1), "POST", CHECK_HTU, future_iat)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 409
        assert body["reason"] == "iat_skew"

    def test_t92ac16_jka77f3_iat_past_skew_denied(self) -> None:
        """A proof timestamped far in the past is denied iat_skew."""
        kp = generate_keypair(f"iat-past:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "iat-past")
        session = derive_session(SEED, "iat-past")
        now = 1_800_160_000
        open_proof = build_proof(kp, derive_jti(SEED, "iat-past", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            past_iat = now - 900
            check_proof_str = build_proof(kp, derive_jti(SEED, "iat-past", 1), "POST", CHECK_HTU, past_iat)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 409
        assert body["reason"] == "iat_skew"

    def test_t92ac16_jka77f3_iat_within_tolerance_admits(self) -> None:
        """A proof inside the configured skew window admits normally."""
        kp = generate_keypair(f"iat-ok:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "iat-ok")
        session = derive_session(SEED, "iat-ok")
        now = 1_800_170_000
        open_proof = build_proof(kp, derive_jti(SEED, "iat-ok", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            check_proof_str = build_proof(kp, derive_jti(SEED, "iat-ok", 1), "POST", CHECK_HTU, now - 10)
            status, body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert status == 200
        assert body["verdict"] == "admit"


class TestAlgAndSignaturePolicy:
    def test_t92ac16_jka77f3_alg_rejected_for_non_es256(self) -> None:
        """A header alg other than ES256 is denied alg_rejected before the
        signature is even ingested."""
        kp = generate_keypair(f"alg-bad:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "alg-bad")
        session = derive_session(SEED, "alg-bad")
        now = 1_800_180_000
        open_proof = build_proof(kp, derive_jti(SEED, "alg-bad", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            good_proof = build_proof(kp, derive_jti(SEED, "alg-bad", 1), "POST", CHECK_HTU, now)
            tampered = tamper_header(good_proof, alg="HS256")
            status, body = check_proof(principal, session, ticket, tampered, now_unix=now)
        assert status == 409
        assert body["reason"] == "alg_rejected"

    def test_t92ac16_jka77f3_bad_signature_denied(self) -> None:
        """A corrupted signature is denied bad_signature."""
        kp = generate_keypair(f"sig-bad:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "sig-bad")
        session = derive_session(SEED, "sig-bad")
        now = 1_800_190_000
        open_proof = build_proof(kp, derive_jti(SEED, "sig-bad", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            good_proof = build_proof(kp, derive_jti(SEED, "sig-bad", 1), "POST", CHECK_HTU, now)
            tampered = tamper_signature(good_proof)
            status, body = check_proof(principal, session, ticket, tampered, now_unix=now)
        assert status == 409
        assert body["reason"] == "bad_signature"

    def test_t92ac16_jka77f3_malformed_proof_denied_bad_signature(self) -> None:
        """A structurally malformed proof (not 3 dot-separated segments) is
        also denied bad_signature."""
        kp = generate_keypair(f"malformed:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "malformed")
        session = derive_session(SEED, "malformed")
        now = 1_800_200_000
        open_proof = build_proof(kp, derive_jti(SEED, "malformed", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            status, body = check_proof(principal, session, ticket, "not-a-proof", now_unix=now)
        assert status == 409
        assert body["reason"] == "bad_signature"


class TestBindTicketPolicy:
    def test_t92ac16_jka77f3_ticket_invalid_denied(self) -> None:
        """A wrong bind ticket string is denied ticket_invalid."""
        kp = generate_keypair(f"ticket-bad:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "ticket-bad")
        session = derive_session(SEED, "ticket-bad")
        now = 1_800_210_000
        open_proof = build_proof(kp, derive_jti(SEED, "ticket-bad", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            open_session(principal, session, open_proof, now_unix=now)
            check_proof_str = build_proof(kp, derive_jti(SEED, "ticket-bad", 1), "POST", CHECK_HTU, now)
            status, body = check_proof(principal, session, "0" * 64, check_proof_str, now_unix=now)
        assert status == 409
        assert body["reason"] == "ticket_invalid"

    def test_t92ac16_jka77f3_unopened_session_check_status_400(self) -> None:
        """Checking against a (principal, session) that never opened is 400."""
        with runtime_session():
            status, body = check_proof("svc-never-opened", "sess-never-opened", "deadbeef", "x.y.z", now_unix=1_800_220_000)
        assert status == 400


class TestJTINonceWindow:
    def test_t92ac16_jka77f3_replayed_jti_denied_second_time(self) -> None:
        """Ingesting the exact same proof twice denies jti_replay on reuse."""
        kp = generate_keypair(f"replay:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "replay")
        session = derive_session(SEED, "replay")
        now = 1_800_230_000
        open_proof = build_proof(kp, derive_jti(SEED, "replay", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            check_proof_str = build_proof(kp, derive_jti(SEED, "replay", 1), "POST", CHECK_HTU, now)
            first_status, first_body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
            second_status, second_body = check_proof(principal, session, ticket, check_proof_str, now_unix=now)
        assert first_status == 200 and first_body["verdict"] == "admit"
        assert second_status == 409
        assert second_body["reason"] == "jti_replay"

    def test_t92ac16_jka77f3_different_jkt_same_jti_not_replay(self) -> None:
        """The nonce window is scoped per jkt: two independently-opened
        sessions with different pinned keys may reuse the same jti string
        without tripping replay detection on either one."""
        kp_a = generate_keypair(f"replay-scope-a:{SEED}".encode("utf-8"))
        kp_b = generate_keypair(f"replay-scope-b:{SEED}".encode("utf-8"))
        principal_a = derive_principal(SEED, "replay-scope-a")
        principal_b = derive_principal(SEED, "replay-scope-b")
        session_a = derive_session(SEED, "replay-scope-a")
        session_b = derive_session(SEED, "replay-scope-b")
        now = 1_800_240_000
        shared_jti = derive_jti(SEED, "replay-scope-shared", 0)
        with runtime_session():
            _, opened_a = open_session(principal_a, session_a, build_proof(kp_a, derive_jti(SEED, "replay-scope-a", 0), "POST", OPEN_HTU, now), now_unix=now)
            _, opened_b = open_session(principal_b, session_b, build_proof(kp_b, derive_jti(SEED, "replay-scope-b", 0), "POST", OPEN_HTU, now), now_unix=now)
            proof_a = build_proof(kp_a, shared_jti, "POST", CHECK_HTU, now)
            proof_b = build_proof(kp_b, shared_jti, "POST", CHECK_HTU, now)
            status_a, body_a = check_proof(principal_a, session_a, opened_a["bind_ticket"], proof_a, now_unix=now)
            status_b, body_b = check_proof(principal_b, session_b, opened_b["bind_ticket"], proof_b, now_unix=now)
        assert status_a == 200 and body_a["verdict"] == "admit"
        assert status_b == 200 and body_b["verdict"] == "admit"


class TestChainheadStaging:
    def test_t92ac16_jka77f3_chainhead_file_appears_post_check(self) -> None:
        """A successful ingest stages chainhead.json per the
        chainhead-stage.md schema."""
        sc = scenario_clean_check_stream(SEED, OPEN_HTU, CHECK_HTU)
        now = 1_800_250_000
        with runtime_session():
            _, opened = open_session(sc.principal, sc.session, sc.open_proof(now), now_unix=now)
            proof, _ = sc.check_proof(1, now)
            check_proof(sc.principal, sc.session, opened["bind_ticket"], proof, now_unix=now)
            assert SNAPSHOT.is_file()
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["version"] == 1
        assert snap["principal"] == sc.principal
        assert snap["session"] == sc.session

    def test_t92ac16_jka77f3_chainevents_preserve_ascending_order(self) -> None:
        """chain_events must stay in the order decisions actually happened
        in (ascending seq), never resorted by jti string."""
        kp = generate_keypair(f"order:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "order")
        session = derive_session(SEED, "order")
        now = 1_800_260_000
        open_proof = build_proof(kp, derive_jti(SEED, "order", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            proof1 = build_proof(kp, "zzz-first-jti", "POST", CHECK_HTU, now)
            check_proof(principal, session, ticket, proof1, now_unix=now)
            proof2 = build_proof(kp, "aaa-second-jti", "POST", CHECK_HTU, now)
            check_proof(principal, session, ticket, proof2, now_unix=now)
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        events = snap["chain_events"]
        assert [e["jti"] for e in events] == ["zzz-first-jti", "aaa-second-jti"]
        assert [e["seq"] for e in events] == sorted(e["seq"] for e in events)

    def test_t92ac16_jka77f3_chainseq_increments_each_decision(self) -> None:
        """chain_seq increments by one for every staged decision, admit or
        deny."""
        kp = generate_keypair(f"seqinc:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "seqinc")
        session = derive_session(SEED, "seqinc")
        now = 1_800_270_000
        open_proof = build_proof(kp, derive_jti(SEED, "seqinc", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            proof1 = build_proof(kp, derive_jti(SEED, "seqinc", 1), "POST", CHECK_HTU, now)
            check_proof(principal, session, ticket, proof1, now_unix=now)
            first_seq = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["chain_seq"]
            check_proof(principal, session, ticket, proof1, now_unix=now)  # replay -> deny, still stages
            second_seq = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["chain_seq"]
        assert second_seq == first_seq + 1


class TestDenyLedgerSeal:
    def test_t92ac16_jka77f3_commit_jti_replay_count_not_zeroed(self) -> None:
        """The sealed ledger's jti_replay deny count must equal the chainhead
        snapshot's — sealing never zeroes an individual deny reason."""
        kp = generate_keypair(f"seal-replay:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "seal-replay")
        session = derive_session(SEED, "seal-replay")
        now = 1_800_280_000
        open_proof = build_proof(kp, derive_jti(SEED, "seal-replay", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            proof = build_proof(kp, derive_jti(SEED, "seal-replay", 1), "POST", CHECK_HTU, now)
            check_proof(principal, session, ticket, proof, now_unix=now)
            check_proof(principal, session, ticket, proof, now_unix=now)
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            ledger = commit(principal, session)
        assert snap["deny_totals"]["jti_replay"] == 1
        assert ledger["deny_totals"]["jti_replay"] == 1

    def test_t92ac16_jka77f3_sealed_ledger_has_no_decoy_field(self) -> None:
        """The sealed ledger must contain exactly the deny-ledger-seal.md
        schema fields — no decoy or debug metric leaks through export."""
        sc = scenario_clean_check_stream(SEED, OPEN_HTU, CHECK_HTU)
        now = 1_800_290_000
        with runtime_session():
            _, opened = open_session(sc.principal, sc.session, sc.open_proof(now), now_unix=now)
            proof, _ = sc.check_proof(1, now)
            check_proof(sc.principal, sc.session, opened["bind_ticket"], proof, now_unix=now)
            ledger = commit(sc.principal, sc.session)
        allowed_keys = {
            "principal", "session", "jkt", "admitted_total", "denied_total",
            "deny_totals", "chain_seq", "chain_head", "seal_digest",
        }
        assert set(ledger.keys()) == allowed_keys
        assert "decoy_entropy_score" not in ledger

    def test_t92ac16_jka77f3_deny_totals_has_all_eight_reason_keys(self) -> None:
        """deny_totals always carries all eight documented deny reasons,
        even when every check so far has succeeded."""
        sc = scenario_clean_check_stream(SEED, OPEN_HTU, CHECK_HTU)
        now = 1_800_300_000
        with runtime_session():
            _, opened = open_session(sc.principal, sc.session, sc.open_proof(now), now_unix=now)
            proof, _ = sc.check_proof(1, now)
            check_proof(sc.principal, sc.session, opened["bind_ticket"], proof, now_unix=now)
            ledger = commit(sc.principal, sc.session)
        assert set(ledger["deny_totals"].keys()) == set(DENY_REASONS)

    def test_t92ac16_jka77f3_recommit_is_idempotent(self) -> None:
        """Re-committing an unchanged chainhead snapshot writes byte-identical
        ledger JSON (idempotent export)."""
        sc = scenario_clean_check_stream(SEED, OPEN_HTU, CHECK_HTU)
        now = 1_800_310_000
        with runtime_session():
            _, opened = open_session(sc.principal, sc.session, sc.open_proof(now), now_unix=now)
            proof, _ = sc.check_proof(1, now)
            check_proof(sc.principal, sc.session, opened["bind_ticket"], proof, now_unix=now)
            commit(sc.principal, sc.session)
            first_bytes = LEDGER.read_bytes()
            commit(sc.principal, sc.session)
            second_bytes = LEDGER.read_bytes()
        assert first_bytes == second_bytes

    def test_t92ac16_jka77f3_commit_missing_open_status_400(self) -> None:
        """Committing a principal/session that never opened (no chainhead
        snapshot to export) is HTTP 400."""
        with runtime_session():
            status, _ = http_json("POST", "/gate/audit/commit", {"principal": "svc-nope", "session": "sess-nope"})
        assert status == 400


class TestPinRegistryFixtureOverride:
    def test_t92ac16_jka77f3_default_registry_allows_any_jkt(self) -> None:
        """With no JKTADMIT_PIN_DIR override, the shipped open registry at
        /opt/verifier-fixtures/jktadmit_hidden allows any jkt to open."""
        kp = generate_keypair(f"open-registry:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "open-registry")
        session = derive_session(SEED, "open-registry")
        now = 1_800_320_000
        proof = build_proof(kp, derive_jti(SEED, "open-registry", 0), "POST", OPEN_HTU, now)
        with runtime_session():
            status, _ = open_session(principal, session, proof, now_unix=now, expect_ok=False)
        assert status == 200

    def test_t92ac16_jka77f3_jktadmit_pin_dir_override_restricts_open(self) -> None:
        """Setting JKTADMIT_PIN_DIR to a directory with a restrictive
        allowlist (that excludes this key's jkt) must override the shipped
        default at /opt/verifier-fixtures/jktadmit_hidden and deny the open."""
        kp = generate_keypair(f"override-deny:{SEED}".encode("utf-8"))
        principal = derive_principal(SEED, "override-deny")
        session = derive_session(SEED, "override-deny")
        now = 1_800_330_000
        proof = build_proof(kp, derive_jti(SEED, "override-deny", 0), "POST", OPEN_HTU, now)
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "jkt_pins.json"
            registry_path.write_text(
                json.dumps({"mode": "allowlist", "jkts": ["0" * 64]}),
                encoding="utf-8",
            )
            with runtime_session(env_overrides={"JKTADMIT_PIN_DIR": tmp}):
                status, body = open_session(principal, session, proof, now_unix=now, expect_ok=False)
        assert status == 409
        assert "jkt_not_registered" in body.get("raw", "")


class TestHiddenFixtureRefmath:
    def test_t92ac16_jka77f3_hidden_case_replay_math_equals_expected(self) -> None:
        """The hidden fixture at /opt/verifier-fixtures/jktadmit_hidden/hidden_case.json
        pins a seed and expected admit/deny totals for an unseen scenario:
        two clean checks, one replay of the first, then one more clean
        check."""
        spec = json.loads(Path("/opt/verifier-fixtures/jktadmit_hidden/hidden_case.json").read_text(encoding="utf-8"))
        seed = spec["verifier_seed"]
        kp = generate_keypair(f"hidden-key:{seed}".encode("utf-8"))
        principal = derive_principal(seed, "hidden")
        session = derive_session(seed, "hidden")
        now = 1_800_340_000
        open_proof = build_proof(kp, derive_jti(seed, "hidden:open", 0), "POST", OPEN_HTU, now)
        with seeded_runtime(seed):
            _, opened = open_session(principal, session, open_proof, now_unix=now)
            ticket = opened["bind_ticket"]
            jti1 = derive_jti(seed, "hidden:check", 1)
            jti2 = derive_jti(seed, "hidden:check", 2)
            jti3 = derive_jti(seed, "hidden:check", 3)
            proof1 = build_proof(kp, jti1, "POST", CHECK_HTU, now)
            proof2 = build_proof(kp, jti2, "POST", CHECK_HTU, now)
            proof3 = build_proof(kp, jti3, "POST", CHECK_HTU, now)
            check_proof(principal, session, ticket, proof1, now_unix=now)
            check_proof(principal, session, ticket, proof2, now_unix=now)
            check_proof(principal, session, ticket, proof1, now_unix=now)  # replay of jti1
            check_proof(principal, session, ticket, proof3, now_unix=now)
            ledger = commit(principal, session)
        assert ledger["admitted_total"] == spec["expected_admitted_total"]
        assert ledger["denied_total"] == spec["expected_denied_total"]
        assert ledger["deny_totals"][spec["expected_deny_reason"]] == spec["expected_deny_count"]

    def test_t92ac16_jka77f3_hidden_fixture_directory_is_the_documented_default(self) -> None:
        """The gate's documented default pin directory is
        /opt/verifier-fixtures/jktadmit_hidden, and it ships a jkt_pins.json
        plus hidden_case.json used by the hidden-scenario checks above."""
        base = Path("/opt/verifier-fixtures/jktadmit_hidden")
        assert (base / "jkt_pins.json").is_file()
        assert (base / "hidden_case.json").is_file()


class TestInstructionOutputPaths:
    def test_t92ac16_jka77f3_instruction_output_locations_exist(self) -> None:
        """Staging and export paths named in the operator instructions are
        written on a successful open -> check -> commit ingest run."""
        sc = scenario_clean_check_stream(SEED, OPEN_HTU, CHECK_HTU)
        now = 1_800_350_000
        with runtime_session():
            _, opened = open_session(sc.principal, sc.session, sc.open_proof(now), now_unix=now)
            proof, _ = sc.check_proof(1, now)
            check_proof(sc.principal, sc.session, opened["bind_ticket"], proof, now_unix=now)
            commit(sc.principal, sc.session)
        assert str(SNAPSHOT) == "/app/state/chainhead.json"
        assert str(LEDGER) == "/app/output/deny-ledger.json"
        assert SNAPSHOT.is_file()
        assert LEDGER.is_file()


@pytest.mark.parametrize("extra_seed", EXTRA_SEEDS)
def test_t92ac16_jka77f3_seed_matrix_clean_check_stream(extra_seed: str) -> None:
    """Mutated identities per seed block static ledger JSON shortcuts: each
    seed derives an independent principal/session/keypair and must admit
    cleanly and seal with admitted_total == 1."""
    kp = generate_keypair(f"matrix-key:{extra_seed}".encode("utf-8"))
    principal = derive_principal(extra_seed, "matrix")
    session = derive_session(extra_seed, "matrix")
    now = 1_800_360_000 + (seed_mix(extra_seed, "matrix:ms") % 100)
    open_proof = build_proof(kp, derive_jti(extra_seed, "matrix", 0), "POST", OPEN_HTU, now)
    with seeded_runtime(extra_seed):
        _, opened = open_session(principal, session, open_proof, now_unix=now)
        proof = build_proof(kp, derive_jti(extra_seed, "matrix", 1), "POST", CHECK_HTU, now)
        check_proof(principal, session, opened["bind_ticket"], proof, now_unix=now)
        ledger = commit(principal, session)
    assert ledger["admitted_total"] == 1
    assert ledger["denied_total"] == 0
