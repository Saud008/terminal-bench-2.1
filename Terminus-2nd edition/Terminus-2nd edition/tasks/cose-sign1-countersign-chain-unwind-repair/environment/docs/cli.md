# CLI surface

Binary: cose-audit (installed to /usr/local/bin/cose-audit after build).

## ingest

Required flags:

- --input PATH — COSE Sign1 bundle file (.cose)
- --ledger PATH — SQLite ledger (created if missing)
- --staging PATH — JSON staging snapshot path

Writes staging JSON per staging-schema.md and upserts a ledger row keyed by SHA-256 of the input bytes. Re-ingest of identical bytes must not increase ingest_count.

Exit 0 on success, 1 on parse/IO errors.

## export

Required flags:

- --ledger PATH — same SQLite ledger used by ingest
- --staging PATH — same staging path used with ingest (required flag; export unwinds from ledger-stored COSE bytes, not by re-reading this file)
- --manifest PATH — output JSON manifest per manifest-schema.md

Reads all ledger rows in ingest order, unwinds counter-signature chains from stored bundle bytes, and writes manifest. Exit 0 when manifest written, 2 when ledger empty.

## Environment

TB3_COSE_DIR — when set to an absolute directory, ingest --input must be a basename resolved under that directory only.
