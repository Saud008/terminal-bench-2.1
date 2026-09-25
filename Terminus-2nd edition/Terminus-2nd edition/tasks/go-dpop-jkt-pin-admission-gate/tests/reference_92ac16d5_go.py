"""Independent DPoP proof chainhead refmath for the jktadmit admission gate."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass, field

# NIST P-256 (secp256r1) domain parameters, parsed from hex strings (rather
# than long literal int constants) so the value is easy to diff and cannot
# silently lose digits in transcription. Cross-checked byte-for-byte against
# Go's crypto/elliptic.P256().Params() so signatures produced here verify
# against the shipped jktadmit binary.
P256_P = int("ffffffff00000001000000000000000000000000ffffffffffffffffffffffff", 16)
P256_N = int("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551", 16)
P256_A = P256_P - 3
P256_B = int("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b", 16)
P256_GX = int("6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296", 16)
P256_GY = int("4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5", 16)
P256_G = (P256_GX, P256_GY)

assert P256_P.bit_length() == 256
assert (P256_GY * P256_GY - (P256_GX**3 + P256_A * P256_GX + P256_B)) % P256_P == 0

GRACE_SKEW_SEC = 30
DEFAULT_JTI_WINDOW_SEC = 120

DENY_REASONS = (
    "ticket_invalid",
    "alg_rejected",
    "bad_signature",
    "jkt_mismatch",
    "htm_mismatch",
    "htu_mismatch",
    "iat_skew",
    "jti_replay",
)


def _inv_mod(x: int, m: int) -> int:
    return pow(x % m, m - 2, m)


def _point_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P256_P == 0:
        return None
    if p1 == p2:
        lam = ((3 * x1 * x1 + P256_A) * _inv_mod(2 * y1, P256_P)) % P256_P
    else:
        lam = ((y2 - y1) * _inv_mod((x2 - x1) % P256_P, P256_P)) % P256_P
    x3 = (lam * lam - x1 - x2) % P256_P
    y3 = (lam * (x1 - x3) - y1) % P256_P
    return (x3, y3)


def _scalar_mult(k: int, point):
    result = None
    addend = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _int_to_32(x: int) -> bytes:
    return x.to_bytes(32, "big")


@dataclass
class KeyPair:
    """A single ephemeral EC P-256 keypair used to mint DPoP proofs."""

    d: int
    x: int
    y: int

    @property
    def jwk(self) -> dict:
        return {
            "kty": "EC",
            "crv": "P-256",
            "x": _b64url(_int_to_32(self.x)),
            "y": _b64url(_int_to_32(self.y)),
        }

    def jkt(self) -> str:
        return thumbprint(self.jwk)


def generate_keypair(seed_material: bytes) -> KeyPair:
    """Derive a deterministic-but-valid P-256 keypair from arbitrary bytes."""
    d = (int.from_bytes(hashlib.sha256(seed_material).digest(), "big") % (P256_N - 1)) + 1
    point = _scalar_mult(d, P256_G)
    assert point is not None
    x, y = point
    return KeyPair(d=d, x=x, y=y)


def thumbprint(jwk: dict) -> str:
    """RFC 7638-style thumbprint, hex(sha256(canonical member string))."""
    canonical = json.dumps(
        {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]},
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _sign(kp: KeyPair, message: bytes) -> bytes:
    z = int.from_bytes(hashlib.sha256(message).digest(), "big")
    while True:
        k = secrets.randbelow(P256_N - 1) + 1
        point = _scalar_mult(k, P256_G)
        if point is None:
            continue
        r = point[0] % P256_N
        if r == 0:
            continue
        s = (_inv_mod(k, P256_N) * (z + r * kp.d)) % P256_N
        if s == 0:
            continue
        return _int_to_32(r) + _int_to_32(s)


def build_proof(kp: KeyPair, jti: str, htm: str, htu: str, iat: int) -> str:
    """Mint a compact header.payload.signature DPoP proof."""
    header = {"typ": "dpop+jwt", "alg": "ES256", "jwk": kp.jwk}
    payload = {"jti": jti, "htm": htm, "htu": htu, "iat": iat}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = _sign(kp, signing_input)
    return f"{header_b64}.{payload_b64}.{_b64url(sig)}"


def tamper_header(proof: str, **overrides) -> str:
    """Return proof with header fields overridden, keeping payload/signature.

    Useful for alg_rejected checks where the signature is expected to be
    invalid anyway once the alg no longer matches the original key/message.
    """
    header_b64, payload_b64, sig_b64 = proof.split(".")
    header = json.loads(base64.urlsafe_b64decode(header_b64 + "=="))
    header.update(overrides)
    new_header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    return f"{new_header_b64}.{payload_b64}.{sig_b64}"


def tamper_signature(proof: str) -> str:
    """Flip the last signature byte so the proof becomes bad_signature."""
    header_b64, payload_b64, sig_b64 = proof.split(".")
    raw = bytearray(base64.urlsafe_b64decode(sig_b64 + "=="))
    raw[-1] ^= 0xFF
    return f"{header_b64}.{payload_b64}.{_b64url(bytes(raw))}"


def seed_mix(seed: str, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def derive_principal(seed: str, scenario: str) -> str:
    return f"svc-{seed_mix(seed, scenario) & 0xFFFF:04x}"


def derive_session(seed: str, scenario: str) -> str:
    return f"sess-{seed_mix(seed, scenario + ':sess') & 0xFFFF:04x}"


def derive_jti(seed: str, scenario: str, ordinal: int) -> str:
    return f"jti-{seed_mix(seed, f'{scenario}:{ordinal}') & 0xFFFFFF:06x}"


@dataclass
class GateModel:
    """Independent refmath mirror of the admission-gate deny/admit ledger.

    Every deny/admit ingested here must line up with what jktadmit reports
    after staging a chainhead snapshot and sealing the deny ledger.
    """

    principal: str
    session: str
    jkt: str
    admitted_total: int = 0
    denied_total: int = 0
    deny_totals: dict = field(default_factory=lambda: {r: 0 for r in DENY_REASONS})
    chain_seq: int = 0
    chain_head: str = ""
    chain_events: list = field(default_factory=list)

    def _advance_head(self, verdict_token: str) -> None:
        prev = self.chain_head
        msg = f"{prev}:{self.principal}:{self.session}:{self.chain_seq}:{verdict_token}"
        self.chain_head = hashlib.sha256(msg.encode("utf-8")).hexdigest()

    def record_admit(self, jti: str) -> None:
        self.chain_seq += 1
        self.admitted_total += 1
        self.chain_events.append({"seq": self.chain_seq, "jti": jti, "verdict": "admit"})
        self._advance_head(f"admit:{jti}")

    def record_deny(self, jti: str, reason: str) -> None:
        self.chain_seq += 1
        self.denied_total += 1
        self.deny_totals[reason] = self.deny_totals.get(reason, 0) + 1
        self.chain_events.append({"seq": self.chain_seq, "jti": jti, "verdict": "deny", "reason": reason})
        self._advance_head(f"deny:{reason}")

    def sealed_ledger(self) -> dict:
        ledger = {
            "principal": self.principal,
            "session": self.session,
            "jkt": self.jkt,
            "admitted_total": self.admitted_total,
            "denied_total": self.denied_total,
            "deny_totals": dict(self.deny_totals),
            "chain_seq": self.chain_seq,
            "chain_head": self.chain_head,
        }
        canonical = json.dumps(ledger, sort_keys=True, separators=(",", ":"))
        ledger["seal_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return ledger


@dataclass
class Scenario:
    """A fully-specified principal/session with a keypair and check script."""

    principal: str
    session: str
    keypair: KeyPair
    open_htu: str
    check_htu: str
    seed: str
    label: str
    model: GateModel = field(init=False)

    def __post_init__(self) -> None:
        self.model = GateModel(principal=self.principal, session=self.session, jkt=self.keypair.jkt())

    def open_proof(self, iat: int, jti: str | None = None) -> str:
        jti = jti or derive_jti(self.seed, self.label + ":open", 0)
        return build_proof(self.keypair, jti, "POST", self.open_htu, iat)

    def check_proof(self, ordinal: int, iat: int, *, htm: str = "POST", htu: str | None = None, jti: str | None = None) -> tuple[str, str]:
        jti = jti or derive_jti(self.seed, self.label + ":check", ordinal)
        proof = build_proof(self.keypair, jti, htm, htu or self.check_htu, iat)
        return proof, jti


def scenario_clean_check_stream(seed: str, open_htu: str, check_htu: str) -> Scenario:
    """Three consecutive fresh proofs: every one of them must admit."""
    principal = derive_principal(seed, "clean")
    session = derive_session(seed, "clean")
    kp = generate_keypair(f"clean-key:{seed}".encode("utf-8"))
    sc = Scenario(principal, session, kp, open_htu, check_htu, seed, "clean")
    return sc


def scenario_replay_then_fresh(seed: str, open_htu: str, check_htu: str) -> Scenario:
    """A jti is replayed once, then a distinct fresh jti is admitted."""
    principal = derive_principal(seed, "replay")
    session = derive_session(seed, "replay")
    kp = generate_keypair(f"replay-key:{seed}".encode("utf-8"))
    sc = Scenario(principal, session, kp, open_htu, check_htu, seed, "replay")
    return sc
