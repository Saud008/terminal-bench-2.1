# Snapshot guard contract

Before publish selection runs, `staging.VerifySnapshot` must confirm that a negotiation snapshot has not drifted from its recorded fields.

## Request ordering on `GET /resource/{id}`

When `/app/state/negotiation.snapshot.json` already exists at the start of a request:

1. Load that on-disk snapshot and call `VerifySnapshot` **before** ingest rewrites the file and **before** the response cache is consulted.
2. If verification fails, return `406 Not Acceptable` with `X-Cache: MISS`. Do not overwrite the snapshot or serve a cached `200`/`406` on that request.

When no snapshot file exists yet, skip this pre-check and proceed with ingest.

## When it runs

- **Pre-request guard** — the resource handler loads the existing on-disk snapshot (if present) and calls `VerifySnapshot` before ingest or cache lookup.
- **Publish guard** — `staging.SelectFromSnapshot` calls `VerifySnapshot` on the in-memory snapshot from the current ingest before ranking or scoring variants.
- **Admin verify** — `GET /admin/negotiation/verify` reloads `/app/state/negotiation.snapshot.json` and reports whether the stored `negotiation_digest` matches a recomputation using the same digest function documented in `/app/docs/negotiation-snapshot.md`.

## Failure semantics

When verification fails, publish must treat the snapshot as unusable: return no match so the HTTP handler emits `406 Not Acceptable`. The verify endpoint returns HTTP 200 with `{"aligned": false}`.

When verification succeeds, publish proceeds normally and the verify endpoint returns `{"aligned": true}`.

## Digest function

Use the exported `staging.Digest` helper when recording, verifying, and recomputing `negotiation_digest`. Do not duplicate digest logic in another module.
