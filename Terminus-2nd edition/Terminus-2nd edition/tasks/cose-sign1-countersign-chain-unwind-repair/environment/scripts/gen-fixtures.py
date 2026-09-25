#!/usr/bin/env python3
"""Generate COSE Sign1 fixtures with counter-signatures (deterministic keys)."""

from __future__ import annotations

import json
import pathlib
from typing import Any

import cbor2
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

OUT = pathlib.Path("/app/fixtures/cose")
HIDDEN = pathlib.Path("/app/opt/verifier-fixtures")
OUT.mkdir(parents=True, exist_ok=True)
HIDDEN.mkdir(parents=True, exist_ok=True)

LABEL_ALG = 1
LABEL_KID = 2
LABEL_CS = 11
LABEL_VENDOR = -1
ALG_ES256 = -7
ALG_ED25519 = -8


def _canonical_protected(items: dict[int, Any]) -> bytes:
    ordered: dict[int, Any] = {}
    for label in sorted(items.keys(), key=lambda k: cbor2.dumps(k, canonical=True)):
        ordered[label] = items[label]
    return cbor2.dumps(ordered, canonical=True)


def _sig_structure(protected: bytes, external_aad: bytes, payload: bytes, sig_field: bytes) -> bytes:
    return cbor2.dumps(
        ["Signature1", protected, external_aad, payload, sig_field],
        canonical=True,
    )


def _ed25519_key(seed: bytes) -> tuple[ed25519.Ed25519PrivateKey, bytes]:
    sk = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pk = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sk, pk


def _es256_key(seed: bytes) -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    sk = ec.derive_private_key(int.from_bytes(seed, "big") % (2**256), ec.SECP256R1())
    pk = sk.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return sk, pk


def _sign_ed25519(sk: ed25519.Ed25519PrivateKey, msg: bytes) -> bytes:
    return sk.sign(msg)


def _sign_es256(sk: ec.EllipticCurvePrivateKey, msg: bytes) -> bytes:
    return sk.sign(msg, ec.ECDSA(hashes.SHA256()))


def _encode_sign1(
    protected: bytes,
    unprotected: dict[Any, Any],
    payload: bytes,
    signature: bytes,
) -> bytes:
    return cbor2.dumps([protected, unprotected, payload, signature], canonical=True)


def _encode_countersign(protected: bytes, unprotected: dict[Any, Any], signature: bytes) -> list[Any]:
    return [protected, unprotected, signature]


def _build_payload(message: str, anchors: dict[str, bytes]) -> bytes:
    body = {
        "message": message,
        "anchors": {k: v.hex() for k, v in anchors.items()},
    }
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode()


def build_bundle(
    name: str,
    outer_alg: int,
    outer_kid: str,
    outer_sk_seed: bytes,
    outer_signer: str,
    counters: list[tuple[str, int, bytes, str]],
    *,
    bad_outer: bool = False,
    bad_cs_index: int | None = None,
    out_dir: pathlib.Path = OUT,
) -> None:
    anchors: dict[str, bytes] = {}
    if outer_signer == "ed25519":
        outer_sk, outer_pk = _ed25519_key(outer_sk_seed)
        anchors[outer_kid] = outer_pk
    else:
        outer_sk, outer_pk = _es256_key(outer_sk_seed)
        anchors[outer_kid] = outer_pk

    cs_entries = []
    for kid, alg, seed, signer in counters:
        if signer == "ed25519":
            sk, pk = _ed25519_key(seed)
        else:
            sk, pk = _es256_key(seed)
        anchors[kid] = pk
        prot = _canonical_protected({LABEL_ALG: alg, LABEL_KID: kid})
        cs_entries.append((prot, sk, alg, signer, kid))

    payload = _build_payload(f"fixture-{name}", anchors)
    outer_prot = _canonical_protected(
        {LABEL_ALG: outer_alg, LABEL_KID: outer_kid, LABEL_VENDOR: b""}
    )
    outer_msg = _sig_structure(outer_prot, b"", payload, b"")
    if outer_signer == "ed25519":
        outer_sig = _sign_ed25519(outer_sk, outer_msg)
    else:
        outer_sig = _sign_es256(outer_sk, outer_msg)
    if bad_outer:
        outer_sig = bytes(b ^ 0x01 for b in outer_sig[:8]) + outer_sig[8:]

    sig_field = outer_prot + cbor2.dumps({}, canonical=True) + outer_sig
    cs_array = []
    for idx, (prot, sk, alg, signer, kid) in enumerate(cs_entries):
        cs_msg = _sig_structure(prot, b"", b"", sig_field)
        if signer == "ed25519":
            sig = _sign_ed25519(sk, cs_msg)
        else:
            sig = _sign_es256(sk, cs_msg)
        if bad_cs_index == idx:
            sig = sig[:-1] + bytes([sig[-1] ^ 0x55])
        cs_array.append(_encode_countersign(prot, {}, sig))

    unprot = {LABEL_CS: cs_array}
    blob = _encode_sign1(outer_prot, unprot, payload, outer_sig)
    (out_dir / f"{name}.cose").write_bytes(blob)


build_bundle(
    "simple-ed25519",
    ALG_ED25519,
    "device",
    b"\x01" * 32,
    "ed25519",
    [],
)

build_bundle(
    "dual-countersign",
    ALG_ED25519,
    "device",
    b"\x02" * 32,
    "ed25519",
    [
        ("beta", ALG_ED25519, b"\x10" * 32, "ed25519"),
        ("alpha", ALG_ES256, b"\x11" * 32, "es256"),
    ],
)

build_bundle(
    "es256-outer",
    ALG_ES256,
    "manufacturer",
    b"\x03" * 32,
    "es256",
    [("witness", ALG_ED25519, b"\x12" * 32, "ed25519")],
)

build_bundle(
    "partial-chain",
    ALG_ED25519,
    "device",
    b"\x04" * 32,
    "ed25519",
    [
        ("audit-a", ALG_ED25519, b"\x20" * 32, "ed25519"),
        ("audit-b", ALG_ES256, b"\x21" * 32, "es256"),
    ],
    bad_cs_index=1,
)

build_bundle(
    "hidden-mixed-order",
    ALG_ED25519,
    "hidden-device",
    b"\x05" * 32,
    "ed25519",
    [
        ("z-last", ALG_ED25519, b"\x30" * 32, "ed25519"),
        ("a-first", ALG_ES256, b"\x31" * 32, "es256"),
        ("m-mid", ALG_ED25519, b"\x32" * 32, "ed25519"),
    ],
    out_dir=HIDDEN,
)

build_bundle(
    "hidden-es256-chain",
    ALG_ES256,
    "hidden-mfg",
    b"\x06" * 32,
    "es256",
    [
        ("cs-ed", ALG_ED25519, b"\x40" * 32, "ed25519"),
        ("cs-ec", ALG_ES256, b"\x41" * 32, "es256"),
    ],
    out_dir=HIDDEN,
)

print(f"generated {len(list(OUT.glob('*.cose')))} public and {len(list(HIDDEN.glob('*.cose')))} hidden fixtures")
