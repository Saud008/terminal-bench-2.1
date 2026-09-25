# Negotiation snapshot staging

Each `GET /resource/{id}` request runs a staged negotiation pipeline before cache lookup and response assembly.

| Stage | Module | Artifact |
|-------|--------|----------|
| 0 Prior guard | `internal/staging/guard.go` | existing `/app/state/negotiation.snapshot.json` (if present) |
| 1 Ingest | `internal/negotiate/prepare.go`, `internal/staging/snapshot.go` | `/app/state/negotiation.snapshot.json` |
| 2 Publish guard | `internal/staging/guard.go` | digest alignment on newly ingested snapshot |
| 3 Publish | `internal/staging/publish.go` | selected variant (in memory) |

When a snapshot file already exists, stage 0 loads and verifies its `negotiation_digest` before ingest overwrites it or the response cache is consulted. On failure the handler returns `406` with `X-Cache: MISS` without rewriting the file or serving a cache hit. See `/app/docs/snapshot-guard-contract.md`.

Stage 1 records both the raw request headers and the prepared negotiation input. Stage 2 verifies the newly written snapshot's `negotiation_digest` before stage 3 selects a catalog variant from the prepared fields only.

## Snapshot schema (version 1)

```json
{
  "snapshot_version": 1,
  "path": "/resource/q-sort",
  "resource_id": "q-sort",
  "raw": {
    "Accept": "application/json;q=0.8, text/plain;q=0.8",
    "Accept-Language": "",
    "Accept-Charset": ""
  },
  "prepared": {
    "Accept": "application/json;q=0.8, text/plain;q=0.8",
    "Accept-Language": "*",
    "Accept-Charset": ""
  },
  "negotiation_digest": "<sha256 hex>"
}
```

Field names in JSON use the same spelling as HTTP headers for the three Accept-family values.

## Raw header preservation

The `raw` object must mirror the incoming request headers exactly (empty string when a header was absent). Do not copy prepared defaults into `raw`, including when `Accept-Charset` was not sent.

## Prepared input

The `prepared` object stores the output of `negotiate.Prepare`. When `Accept-Charset` was absent on the request, `prepared.Accept-Charset` must remain empty so publish can treat charset negotiation as open.

## negotiation_digest

Compute `negotiation_digest` as SHA-256 hex over this pipe-delimited payload:

`path|resource_id|raw.Accept|raw.Accept-Language|raw.Accept-Charset|prepared.Accept|prepared.Accept-Language|prepared.Accept-Charset`

Use the same function when recording and when verifying the snapshot.

## Publish contract

`staging.SelectFromSnapshot` must evaluate variant eligibility, q-weighted scoring, tie-break ordering, and 406 handling using **only** the `prepared` fields from the snapshot. It must not re-read request headers or call `negotiate.Select`.

Selection semantics match `/app/docs/negotiation-contract.md` and `/app/docs/publish-contract.md`. Language prefix matching uses `negotiate.LanguageMatch` and `negotiate.LanguageExactness`.

The legacy `negotiate.Select` helper is not on the request path; repairs must target the staging publish step.
