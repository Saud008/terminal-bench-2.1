# promingest contract

## Remote-write ingest

POST /api/v1/write accepts a Snappy-compressed remote-write block documented in /app/docs/remote-write.md.

Ingest stage order: Snappy decompress, block checksum validate, JSON decode preserving native histogram schema per /app/docs/native-histogram.md, then persist a staging record per /app/docs/staging-ingest.md. Do not relabel or bind exemplars during write handling.

## Snapshot export

GET /api/v1/snapshot?seed=SEED reads the latest staging record for the seed, applies relabel deduplication per /app/docs/relabel-rules.md, binds exemplars per /app/docs/exemplar-binding.md, and returns JSON describing stored series. The response includes the staging sequence under sequence. Buckets include bound exemplar trace IDs per le boundary.

Export must fail closed to an empty series list when no staging record exists for the requested seed.

## Protected paths

Do not edit /app/docs/, /app/fixtures/, or /tests/.
