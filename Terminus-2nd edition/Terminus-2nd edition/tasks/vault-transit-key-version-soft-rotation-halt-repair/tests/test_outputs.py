"""Verifier for vault-transit-key-version-soft-rotation-halt-repair (single-step)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from reference_policy import read_policy
from transit_http import (
    batch_encrypt,
    decrypt,
    delete_version,
    encrypt,
    get_policy,
    load_policy,
    rotate,
    set_halt,
)

APP = Path("/app")
POLICIES = APP / "fixtures" / "policies"
CANONICAL = Path("/opt/verifier-fixtures/policies")
MANIFEST = Path("/opt/verifier-fixtures/policies.sha256")
CATALOG = json.loads((Path(__file__).parent / "catalog.json").read_text(encoding="utf-8"))
BASE = CATALOG["base_url"]
SEED = os.environ.get("VERIFIER_SEED", "17")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(directory: Path, manifest_path: Path) -> None:
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        target = directory / name.strip()
        assert sha256_file(target) == digest


def run_reset() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=False)
    subprocess.run(["bash", str(APP / "scripts" / "start-server.sh")], check=True)


def key_name(prefix: str, suffix: str = "") -> str:
    token = format(int(SEED, 16) % 10000, "04x")
    return f"{prefix}-{token}{suffix}"


@pytest.fixture(autouse=True)
def reset_state() -> None:
    run_reset()


class TestFixtureIntegrity:
    def test_fixture_integrity(self) -> None:
        """Policy fixtures match build-time manifest."""
        verify_manifest(CANONICAL, MANIFEST)
        verify_manifest(POLICIES, MANIFEST)


class TestPolicyMinDecrypt:
    def test_parsed_policy_min_decryption_version(self) -> None:
        """Loaded policy exposes file min_decryption_version."""
        name = key_name(CATALOG["key_prefix"])
        policy_file = CATALOG["policy_file"]
        expected = read_policy(POLICIES / policy_file)
        assert load_policy(BASE, name, policy_file).status == 200
        resp = get_policy(BASE, name)
        assert resp.status == 200
        parsed = resp.json_data["data"]
        assert parsed["min_decryption_version"] == expected["min_decryption_version"]
        assert parsed["min_decryption_version"] == CATALOG["expected_min_decryption_version"]

    def test_decrypt_rejects_below_min_version(self) -> None:
        """Decrypt below min_decryption_version returns 400."""
        name = key_name(CATALOG["key_prefix"], "-dec")
        policy_file = CATALOG["policy_file"]
        load_policy(BASE, name, policy_file)
        enc = encrypt(BASE, name, "legacy-payload", key_version=1)
        assert enc.status == 200
        ciphertext = enc.json_data["data"]["ciphertext"]
        bad = decrypt(BASE, name, ciphertext)
        assert bad.status == 400

    def test_decrypt_allows_at_min_version(self) -> None:
        """Decrypt at min_decryption_version succeeds after rotate."""
        name = key_name(CATALOG["key_prefix"], "-ok")
        policy_file = CATALOG["policy_file"]
        min_ver = CATALOG["expected_min_decryption_version"]
        load_policy(BASE, name, policy_file)
        policy = get_policy(BASE, name)
        assert policy.status == 200
        assert policy.json_data["data"]["min_decryption_version"] == min_ver
        for _ in range(min_ver - 1):
            rotate(BASE, name)
        enc = encrypt(BASE, name, "allowed-payload")
        assert enc.status == 200
        assert int(enc.headers.get("x-vault-key-version", "0")) == min_ver
        assert int(enc.headers.get("x-vault-min-decryption-version", "0")) == min_ver
        ciphertext = enc.json_data["data"]["ciphertext"]
        ok = decrypt(BASE, name, ciphertext)
        assert ok.status == 200
        assert int(ok.headers.get("x-vault-key-version", "0")) == min_ver
        assert int(ok.headers.get("x-vault-min-decryption-version", "0")) == min_ver

    def test_seed_mutated_key_name(self) -> None:
        """Per-run key suffix avoids hard-coded key names."""
        name = key_name(CATALOG["key_prefix"], "-seed")
        policy_file = CATALOG["policy_file"]
        load_policy(BASE, name, policy_file)
        resp = get_policy(BASE, name)
        assert resp.status == 200
        assert resp.json_data["data"]["min_decryption_version"] == read_policy(
            POLICIES / policy_file
        )["min_decryption_version"]


class TestLedgerDeleteAndBatch:
    def test_delete_forbidden_when_policy_disallows(self) -> None:
        """Forbidden delete leaves version active on the key."""
        name = key_name(CATALOG["key_prefix_batch"], "-del")
        load_policy(BASE, name, CATALOG["batch_policy"])
        rotate(BASE, name)
        denied = delete_version(BASE, name, 1)
        assert denied.status == 403
        still = encrypt(BASE, name, "still-there", key_version=1)
        assert still.status == 200
        assert int(still.headers.get("x-vault-key-version", "0")) == 1

    def test_delete_allowed_when_policy_permits(self) -> None:
        """Allowed delete removes the targeted version."""
        name = key_name(CATALOG["key_prefix_delete"], "-ok")
        load_policy(BASE, name, CATALOG["delete_policy"])
        rotate(BASE, name)
        before = encrypt(BASE, name, "v1-data", key_version=1)
        assert before.status == 200
        ok = delete_version(BASE, name, 1)
        assert ok.status == 204
        gone = encrypt(BASE, name, "v1-again", key_version=1)
        assert gone.status == 404

    def test_batch_uses_latest_for_every_item(self) -> None:
        """Batch encrypt picks latest active version for all items regardless of order."""
        name = key_name(CATALOG["key_prefix_batch"], "-batch")
        load_policy(BASE, name, CATALOG["batch_policy"])
        latest = 1
        for _ in range(CATALOG["batch_rotation_count"]):
            resp = rotate(BASE, name)
            assert resp.status == 200
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        items = [
            ("zebra-last", "ctx-z"),
            ("alpha-first", "ctx-a"),
            ("middle-item", "ctx-m"),
        ]
        resp = batch_encrypt(BASE, name, items)
        assert resp.status == 200
        assert int(resp.headers.get("x-vault-key-version", "0")) == latest
        results = resp.json_data["data"]["batch_results"]
        assert len(results) == len(items)
        for row in results:
            assert row["key_version"] == latest

    def test_batch_order_independence(self) -> None:
        """Reversed batch input still uses the same latest version on every item."""
        name = key_name(CATALOG["key_prefix_batch"], "-rev")
        load_policy(BASE, name, CATALOG["batch_policy"])
        latest = 1
        for _ in range(CATALOG["batch_rotation_count"]):
            resp = rotate(BASE, name)
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        forward = batch_encrypt(
            BASE,
            name,
            [("one", "a"), ("two", "b"), ("three", "c")],
        )
        reverse = batch_encrypt(
            BASE,
            name,
            [("three", "c"), ("two", "b"), ("one", "a")],
        )
        assert forward.status == 200 and reverse.status == 200
        f_versions = [r["key_version"] for r in forward.json_data["data"]["batch_results"]]
        r_versions = [r["key_version"] for r in reverse.json_data["data"]["batch_results"]]
        assert f_versions == r_versions == [latest, latest, latest]


class TestConvergentAndSoftHalt:
    def test_convergent_uses_latest_active_version(self) -> None:
        """Convergent encryption must not pin version 1 after rotation."""
        name = key_name(CATALOG["key_prefix_halt"], "-conv")
        load_policy(BASE, name, CATALOG["halt_policy"])
        latest = 1
        for _ in range(CATALOG["halt_rotation_count"]):
            resp = rotate(BASE, name)
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        first = encrypt(BASE, name, "stable-input", context="ctx-1")
        second = encrypt(BASE, name, "stable-input", context="ctx-1")
        assert first.status == 200 and second.status == 200
        assert int(first.headers.get("x-vault-key-version", "0")) == latest
        assert int(second.headers.get("x-vault-key-version", "0")) == latest
        assert (
            first.json_data["data"]["ciphertext"]
            == second.json_data["data"]["ciphertext"]
        )

    def test_soft_halt_blocks_encrypt_on_retired_version(self) -> None:
        """Encrypt targeting a retired version returns 403 with halt header."""
        name = key_name(CATALOG["key_prefix_halt"], "-halt")
        load_policy(BASE, name, CATALOG["halt_policy"])
        latest = 1
        for _ in range(CATALOG["halt_rotation_count"]):
            resp = rotate(BASE, name)
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        halt_after = CATALOG["halt_after"]
        assert set_halt(BASE, name, halt_after).status == 200
        blocked = encrypt(BASE, name, "blocked", key_version=halt_after)
        assert blocked.status == 403
        assert blocked.headers.get("x-vault-halt") == "retired"
        allowed = encrypt(BASE, name, "fresh", key_version=latest)
        assert allowed.status == 200
        assert int(allowed.headers.get("x-vault-key-version", "0")) == latest

    def test_default_encrypt_respects_halt(self) -> None:
        """Default encrypt cannot silently use a retired version when latest is active."""
        name = key_name(CATALOG["key_prefix_halt"], "-default")
        load_policy(BASE, name, CATALOG["halt_policy"])
        latest = 1
        for _ in range(CATALOG["halt_rotation_count"]):
            resp = rotate(BASE, name)
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        set_halt(BASE, name, CATALOG["halt_after"])
        resp = encrypt(BASE, name, "auto-pick")
        assert resp.status == 200
        assert int(resp.headers.get("x-vault-key-version", "0")) == latest

    def test_decrypt_allows_retired_version_after_halt(self) -> None:
        """Retired versions stay decryptable after soft halt blocks new encrypts."""
        name = key_name(CATALOG["key_prefix_halt"], "-dec-retired")
        load_policy(BASE, name, CATALOG["halt_policy"])
        latest = 1
        for _ in range(CATALOG["halt_rotation_count"]):
            resp = rotate(BASE, name)
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        retired = latest - 1
        archived = encrypt(BASE, name, "archive-me", key_version=retired)
        assert archived.status == 200
        assert int(archived.headers.get("x-vault-key-version", "0")) == retired
        ciphertext = archived.json_data["data"]["ciphertext"]
        assert set_halt(BASE, name, CATALOG["halt_after"]).status == 200
        blocked = encrypt(BASE, name, "blocked", key_version=retired)
        assert blocked.status == 403
        assert blocked.headers.get("x-vault-halt") == "retired"
        ok = decrypt(BASE, name, ciphertext)
        assert ok.status == 200
        assert int(ok.headers.get("x-vault-key-version", "0")) == retired

    def test_seed_scoped_key_name(self) -> None:
        """Per-run key suffix avoids static key hardcoding."""
        name = key_name(CATALOG["key_prefix_halt"], "-seed")
        load_policy(BASE, name, CATALOG["halt_policy"])
        latest = 1
        for _ in range(CATALOG["halt_rotation_count"]):
            resp = rotate(BASE, name)
            latest = int(resp.headers.get("x-vault-key-version", "0"))
        resp = encrypt(BASE, name, "probe")
        assert resp.status == 200
        assert int(resp.headers.get("x-vault-key-version", "0")) == latest
