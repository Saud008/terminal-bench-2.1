# jkt thumbprint and proof policy

A proof is a compact string `base64url(header).base64url(payload).base64url(signature)`,
modeled on RFC 9449 DPoP proofs.

## Header

```json
{"typ": "dpop+jwt", "alg": "ES256", "jwk": {"kty": "EC", "crv": "P-256", "x": "...", "y": "..."}}
```

`x` and `y` are base64url (no padding) big-endian 32-byte coordinates.

## Payload

```json
{"jti": "...", "htm": "POST", "htu": "https://jktadmit.local/gate/proof/check", "iat": 1737000000}
```

`iat` is an integer unix second.

## Signature

64 raw bytes: `r` (32 bytes, big-endian) followed by `s` (32 bytes,
big-endian), base64url (no padding) encoded. The signing input is the ASCII
bytes of `base64url(header) + "." + base64url(payload)`, signed with
ECDSA P-256 over its SHA-256 digest (RFC 7518 ES256).

## jkt thumbprint

```
jkt = hex(sha256(canonical_jwk))
canonical_jwk = {"crv":"<crv>","kty":"<kty>","x":"<x>","y":"<y>"}
```

`canonical_jwk` is compact JSON (no insignificant whitespace) with member
names in that exact lexicographic order (`crv`, `kty`, `x`, `y`), per
RFC 7638. The gate's own contract represents the thumbprint as lowercase hex
(64 characters), not base64url.

## Checks, in order

1. `alg` must be exactly `"ES256"`. Anything else is denied `alg_rejected`.
2. The signature must verify against the embedded `jwk`. Malformed encoding,
   unsupported `kty`/`crv`, or a signature that does not verify is denied
   `bad_signature`.
3. **Check only:** the computed `jkt` must equal the jkt pinned for the
   session at open time. Mismatch is denied `jkt_mismatch`.
4. `htm` must equal the route's expected HTTP method
   (`POST` for both `/gate/session/open` and `/gate/proof/check`), compared
   **case-insensitively**. Mismatch is denied `htm_mismatch`.
5. `htu` must equal the route's configured canonical URL (`open_htu` or
   `check_htu` from `/app/config/jktadmit.json`) as an exact string match.
   Mismatch is denied `htu_mismatch`.
6. `iat` must satisfy `abs(now_unix - iat) <= iat_skew_sec`
   (`iat_skew_sec` from config, default 30). A proof timestamped too far in
   **either** the past or the future is denied `iat_skew`.
7. **Check only:** `jti` nonce-window lookup — see
   `/app/docs/jti-nonce-window.md`.

Checks are evaluated in the order above; the first failing check determines
the deny reason.
