# CBOR config bundle format

Input bundles are single CBOR maps read by cbor-audit ingest.

## Top-level map key order

Keys must appear in this insertion order:

1. version (unsigned integer, must be 1)
2. bundle_id (text)
3. diagnostic_tags (array)
4. envelope (tag 24 wrapped policy map)

Reordering keys in the source file is allowed only when the decoded map preserves the order above on the wire.

## diagnostic_tags array

Each element is a map with keys in order:

1. label (text)
2. tag (unsigned integer)

At least one tag entry is required. Labels are opaque identifiers used in attestation reports.

## envelope (CBOR tag 24)

The envelope value is a CBOR tag 24 wrapper around a definite-length byte string containing a CBOR map with keys in order:

1. policy (text, non-empty)
2. nonce (byte string, non-empty)

The byte-string length prefix must encode the exact inner CBOR length. When the inner map encodes to 24 or more bytes, use the one-byte 0x58 length form with the full length (not a truncated or off-by-one value).

Example inner sizes:

- Short policies (under 24 encoded bytes) may use inline byte-string headers.
- Longer policies such as policy-alpha-long-v1 must use 0x58 with the correct length byte.

## Bundled fixtures

/app/fixtures/alpha.cbor — three diagnostic tags, short policy.

/app/fixtures/beta_tagged.cbor — policy string long enough that the tag 24 inner map encodes to 24+ bytes.
