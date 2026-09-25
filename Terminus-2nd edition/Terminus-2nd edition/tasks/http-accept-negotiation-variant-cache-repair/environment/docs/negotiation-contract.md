# Negotiation contract

Normative reference for the variantgate content-negotiation gateway. Staging layout, publish scoring, cache keys, and snapshot guards are defined in the companion docs listed at the end of this file.

Negotiation runs as a staged pipeline: ingest writes /app/state/negotiation.snapshot.json, then publish selects a variant from the staged prepared headers. See /app/docs/negotiation-snapshot.md and /app/docs/publish-contract.md.

## Endpoints

| Method | Path | Role |
|--------|------|------|
| GET | /health | Liveness JSON with {"status":"ok"} |
| GET | /resource/{id} | Negotiated variant body for the active catalog |
| GET | /cache/stats | {"hits":N,"misses":M} integer counters |
| POST | /admin/catalog | Replace in-memory catalog JSON. Clears cached entries and resets hit/miss counters to zero |

## Request headers

GET /resource/{id} reads Accept, Accept-Language, and Accept-Charset.

When a header is absent, prepare applies service defaults before selection runs. Cache keys always use the raw request header values (empty string when absent), not prepared defaults.

### Prepare defaults

| Header | When absent on the request |
|--------|---------------------------|
| Accept | prepared Accept becomes */* |
| Accept-Language | prepared Accept-Language becomes * |
| Accept-Charset | prepared Accept-Charset stays empty (charset negotiation is open) |

Raw snapshot fields must mirror absent headers as empty strings. Never copy prepared defaults into raw.

## Header parsing

Each header value is a comma-separated list of entries. An entry may include a q parameter (for example application/json;q=0.8). When q is omitted, use q=1. Entries with q=0 are excluded.

After parsing, rank entries within each header by q descending. When q is equal, preserve the original header list order (earlier entries rank higher). Use stable sorting.

## Media type matching

Compare Accept entries to each variant media_type case-insensitively after trimming whitespace.

- */* matches any media type.
- type/* matches any media type whose major type equals type.
- Otherwise require an exact media type match.

Specificity for tie-breaks: exact type (2) beats type/* (1) beats */* (0).

## Language matching

Compare Accept-Language entries to each variant language tag case-insensitively.

- * matches any language.
- An exact tag match qualifies.
- A prefix match qualifies when the variant tag starts with the Accept entry plus a hyphen (for example en matches en-US).

Language exactness for tie-breaks: exact tag (2) beats prefix-only match (1) beats no match (0).

## Charset matching

When prepared Accept-Charset is empty, skip charset filtering and score with Accept q times Accept-Language q only.

When Accept-Charset was sent, each candidate variant must match a charset entry. Compare case-insensitively. * matches any charset. Otherwise require an exact charset match. Multiply Accept q, Accept-Language q, and Accept-Charset q for the score.

## Scoring and winner selection

Enumerate eligible combinations of ranked Accept, Accept-Language, and (when sent) Accept-Charset entries against catalog variants. Skip any entry with q=0.

For each eligible variant compute score as the product of the matching q values (use 1.0 for charset q when charset negotiation is open).

Pick the highest score. Tie-break in order:

1. earlier matching Accept entry position in the prepared header list
2. higher media type specificity of the matching Accept entry
3. higher language exactness of the matching Accept-Language entry
4. earlier variant index in the catalog list

When no variant qualifies, publish returns no match and the handler responds with 406 Not Acceptable.

## Response headers

Successful negotiation (200):

- Content-Type: <media-type>; charset=<charset>
- Vary: Accept, Accept-Language, Accept-Charset
- X-Cache: HIT or MISS

406 responses still include Vary: Accept, Accept-Language, Accept-Charset and X-Cache: MISS on first lookup.

## Cached responses

Both 200 and 406 responses may be served from the in-memory cache on repeat lookups. Cache key composition and counter behavior are defined in /app/docs/cache-contract.md.

## Related contracts

- /app/docs/negotiation-snapshot.md — snapshot schema, raw vs prepared fields, negotiation_digest
- /app/docs/publish-contract.md — publish-stage ranking helpers and SelectFromSnapshot inputs
- /app/docs/snapshot-guard-contract.md — pre-request and publish-time digest verification
- /app/docs/cache-contract.md — cache keys, hits/misses, admin catalog reset
