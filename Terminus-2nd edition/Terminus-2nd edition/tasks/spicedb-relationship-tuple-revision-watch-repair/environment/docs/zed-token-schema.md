# Zed token schema

Zed tokens encode a monotonic revision for consistent reads.

## Format

Tokens use prefix z1. followed by base64 raw encoding of eight big-endian bytes.

Example layout:

- bytes 0-7 — uint64 revision in big-endian order

## API usage

POST /v1/tuple/write returns zed_token for the new revision.

POST /v1/check requires zed_token and returns an updated token for head revision.

## Decoding rules

Decode must recover the full 64-bit revision. Truncating to 32 bits breaks correctness when revision exceeds 4294967295.

EncodeRevision and DecodeRevision live in internal/token/zed.go.
