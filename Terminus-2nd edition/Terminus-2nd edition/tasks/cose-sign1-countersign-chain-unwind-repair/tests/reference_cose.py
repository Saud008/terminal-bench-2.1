"""
Independent COSE Sign1 counter-signature reference (mirrors gen-fixtures semantics).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

LABEL_ALG = 1
LABEL_KID = 2
LABEL_CS = 11
ALG_ES256 = -7
ALG_ED25519 = -8


def parse_sign1(data: bytes) -> dict[str, Any]:
    arr = cbor2.loads(data)
    if not isinstance(arr, list) or len(arr) != 4:
        raise ValueError("sign1 shape")
    protected_raw, unprotected, payload, signature = arr
    protected = dict(cbor2.loads(protected_raw))
    if not isinstance(unprotected, dict):
        unprotected = {}
    cs_raw = unprotected.get(LABEL_CS, [])
    counters = []
    for item in cs_raw:
        p_raw, u_map, sig = item
        counters.append(
            {
                "protected_raw": p_raw,
                "protected": dict(cbor2.loads(p_raw)),
                "signature": sig,
            }
        )
    return {
        "protected_raw": protected_raw,
        "protected": protected,
        "unprotected": unprotected,
        "payload": payload,
        "signature": signature,
        "countersigns": counters,
    }


def trust_anchors(payload: bytes) -> dict[str, bytes]:
    body = json.loads(payload.decode())
    return {k: bytes.fromhex(v) for k, v in body["anchors"].items()}


def sig_structure(protected: bytes, external_aad: bytes, payload: bytes, sig_field: bytes) -> bytes:
    return cbor2.dumps(["Signature1", protected, external_aad, payload, sig_field], canonical=True)


def verify_ed25519(pk: bytes, msg: bytes, sig: bytes) -> bool:
    if len(pk) != 32 or len(sig) != 64:
        return False
    key = ed25519.Ed25519PublicKey.from_public_bytes(pk)
    try:
        key.verify(sig, msg)
        return True
    except Exception:
        return False


def verify_es256(pk: bytes, msg: bytes, sig: bytes) -> bool:
    if len(pk) != 65 or pk[0] != 0x04:
        return False
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), pk)
    try:
        key.verify(sig, msg, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def verify_sig(alg: int, pk: bytes, msg: bytes, sig: bytes) -> bool:
    if alg == ALG_ED25519:
        return verify_ed25519(pk, msg, sig)
    if alg == ALG_ES256:
        return verify_es256(pk, msg, sig)
    return False


def protected_key_order(protected: dict[int, Any]) -> list[int]:
    labels = list(protected.keys())
    labels.sort(key=lambda k: cbor2.dumps(k, canonical=True))
    return labels


def unwind_chain(data: bytes) -> dict[str, Any]:
    sign1 = parse_sign1(data)
    anchors = trust_anchors(sign1["payload"])
    outer_alg = sign1["protected"][LABEL_ALG]
    outer_kid = sign1["protected"].get(LABEL_KID, "outer")
    outer_msg = sig_structure(sign1["protected_raw"], b"", sign1["payload"], b"")
    outer_ok = verify_sig(outer_alg, anchors[outer_kid], outer_msg, sign1["signature"])

    sig_field = sign1["protected_raw"] + cbor2.dumps({}, canonical=True) + sign1["signature"]
    unwind = []
    countersign_ok = True
    if not sign1["countersigns"]:
        countersign_ok = True
    for idx, cs in enumerate(sign1["countersigns"]):
        alg = cs["protected"][LABEL_ALG]
        kid = cs["protected"].get(LABEL_KID, f"cs{idx}")
        pk = anchors.get(kid)
        if pk is None:
            ok = False
        else:
            cs_msg = sig_structure(cs["protected_raw"], b"", b"", sig_field)
            ok = verify_sig(alg, pk, cs_msg, cs["signature"])
        if not ok:
            countersign_ok = False
        unwind.append({"index": idx, "kid": kid, "alg": alg, "verify_ok": ok})

    return {
        "input_sha256": __import__("hashlib").sha256(data).hexdigest(),
        "outer_ok": outer_ok,
        "countersign_ok": countersign_ok,
        "partial_retained": outer_ok and not countersign_ok,
        "unwind": unwind,
        "protected_key_order": protected_key_order(sign1["protected"]),
        "countersign_count": len(sign1["countersigns"]),
    }


def reference_manifest(cose_paths: list[Path]) -> dict[str, Any]:
    chains = []
    for path in cose_paths:
        data = path.read_bytes()
        chain = unwind_chain(data)
        if not chain["outer_ok"]:
            continue
        chains.append(
            {
                "input_sha256": chain["input_sha256"],
                "outer_ok": chain["outer_ok"],
                "countersign_ok": chain["countersign_ok"],
                "partial_retained": chain["partial_retained"],
                "unwind": chain["unwind"],
            }
        )
    return {"ledger_rows": len(cose_paths), "chains": chains}


def reference_staging(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    sign1 = parse_sign1(data)
    chain = unwind_chain(data)
    return {
        "input_path": str(path),
        "input_sha256": chain["input_sha256"],
        "payload_len": len(sign1["payload"]),
        "outer_alg": sign1["protected"][LABEL_ALG],
        "outer_kid": sign1["protected"].get(LABEL_KID),
        "countersign_count": len(sign1["countersigns"]),
        "protected_key_order": chain["protected_key_order"],
    }
