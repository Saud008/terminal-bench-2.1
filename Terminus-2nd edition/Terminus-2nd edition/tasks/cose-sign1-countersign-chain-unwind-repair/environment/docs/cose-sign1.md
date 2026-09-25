# COSE Sign1 layout

Each .cose file is one CBOR-encoded COSE_Sign1 array:

[ protected: bstr, unprotected: map, payload: bstr, signature: bstr ]

Protected headers (decoded from protected bstr) must include alg (label 1). Optional kid (label 2). Bundled fixtures may also include a vendor slot (label -1) as an empty byte string.

Counter-signatures live in the unprotected map under label 11 as an array of COSE_Signature elements:

[ protected: bstr, unprotected: map, signature: bstr ]

Each counter-signature protected map must include alg and kid.

Supported algs: -7 (ES256, P-256 ECDSA), -8 (Ed25519).

## Protected header canonicalization

When building Sig_structure or comparing protected maps, header keys must be ordered by the lexicographic order of their encoded CBOR key bytes (RFC 8152 canonical form), not by numeric value alone or decoded string order.

## Sig_structure for Sign1

["Signature1", body_protected, external_aad, payload, signature]

- body_protected is the raw protected headers bstr from the Sign1
- external_aad is empty bstr unless AAD label 3 present in unprotected
- payload is the Sign1 payload bstr

## Sig_structure for counter-signature

["Signature1", body_protected, external_aad, payload, signature]

- body_protected from the counter-signature protected bstr
- payload MUST be empty bstr (zero length)
- signature field is the bstr concatenation: outer protected || outer unprotected || outer signature
