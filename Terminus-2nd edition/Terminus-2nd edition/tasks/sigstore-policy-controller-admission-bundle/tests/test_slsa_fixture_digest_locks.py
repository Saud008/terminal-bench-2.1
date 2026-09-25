"""Fixture digest locks and verifier config byte seal."""

from __future__ import annotations

import slsacip_harness as harness

EXPECTED_SHA256 = {
    "config/slsacip.json": "eed07a069f4c8bd4620c7a491317d9ef8d0d18322fdb91a84db46f7b9a78ae86",
    "fixtures/pull-waves/wave-north.jsonl": "2a79690e80439ea4225da1a411cd92fa6ef42b5396954fe3d330f246b47be0d8",
    "fixtures/pull-waves/wave-east.jsonl": "8d18ca5ae59ada76483b2a3514057007a0690d120eb025252ce7f42551120371",
    "fixtures/pull-waves/wave-south.jsonl": "080cd3ec242b6bafff71eeb996c41a8c808ca17900752015fe72c248bfbb16fd",
    "fixtures/cip-tiers/tier-shore/digest-deny.json": "4bcfa96521c110fd4822c7630386e2c4fdcec8046d85e2102b044140a1598cc1",
    "fixtures/cip-tiers/tier-shore/revocations.json": "a05009f60527322c753eb1c2797fecd990ac5b68f9e4638ac1d2cf5d20c8a377",
    "fixtures/cip-tiers/tier-shore/predicates.json": "c79e998b96162007d33047a4390b46f22130f5fea84e7d5739aa86b1b61007a6",
    "fixtures/cip-tiers/tier-shore/builders.json": "8c152b166e0d0f8cb06ebb5b8ec6c97ea8d4901b9ece9b1c7784499c98667488",
    "fixtures/cip-tiers/tier-ridge/digest-deny.json": "879427db78f391889b678e82d3afab6010286a4a6e52b2aacaa1e19b5c845b84",
    "fixtures/cip-tiers/tier-ridge/builders.json": "597c5abcb1ff016346073e2c4ebb36d38333df145fddaf4a5e39af87e0620d66",
    "fixtures/cip-tiers/tier-mesa/digest-deny.json": "f71d7d9fa2b2d3bb4be05d3ffc35e32825d0adee690118725c3f87d07a17fca7",
    "fixtures/cip-tiers/tier-mesa/revocations.json": "f63fd4bf737433e674cb9be226f4f6b28896f98cba5f5b48b8172bc7e729b025",
    "fixtures/fulcio-roots/prod-fulcio.json": "547d75b6fe8ce3bac621fe064c5454f561b8540ac76e6bb3695cadb325d973ed",
    "fixtures/fulcio-roots/fed-oidc.json": "0b7799ab1505a9154bc23da2103fabd819fc450b01ab0e08b675eb118d89a217",
    "fixtures/fulcio-roots/legacy-ci.json": "c83d0d24fa04895350f70cd58af87604ff00a7d537cd3750046a02989fd42e59",
    "fixtures/attestation-envelopes/env-acme-a1.json": "40173694f26521034a9080208699b6d10490fb4b2345f64d8d62c1a381bab3c8",
    "fixtures/attestation-envelopes/env-fed-d1.json": "67590dccc4ba92da5cd2f6ebcc2a012ccdf4e0e00e96bee89a266bb70e2c5d87",
    "fixtures/attestation-envelopes/env-malware-f1.json": "682018574b6ff04c6b539c9d5ce9b2bf1d5fe00b10fb336b7d656f0e0d861ee5",
}


def test_key_fixture_sha256_locks():
    """Protected fixture bytes must match sealed SHA-256 digests."""
    for rel_path, expected_hash in EXPECTED_SHA256.items():
        actual = harness.fixture_sha256(*rel_path.split("/"))
        assert actual == expected_hash, f"{rel_path} sha256 mismatch (fixture was modified)"


def test_shipped_config_matches_verifier_copy_bytes():
    """Shipped /app/config/slsacip.json must equal verifier-baked copy bytes."""
    shipped = (harness.APP / "config" / "slsacip.json").read_bytes()
    verifier_copy = harness.VERIFIER_CONFIG_PATH.read_bytes()
    assert shipped == verifier_copy
