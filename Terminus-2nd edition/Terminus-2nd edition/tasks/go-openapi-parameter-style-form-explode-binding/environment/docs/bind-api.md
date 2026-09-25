# Paramgate HTTP API

Base URL: `http://127.0.0.1:8080`

## Success

HTTP **200** with JSON:

```json
{"status":"ok","params":{...},"body":{...}}
```

`body` appears only for routes with a request body schema.

The `params` and `body` fields in success responses are sourced from `/app/state/bind-snapshot.json` written during bind (see `/app/docs/bind-snapshot.md`), not from ad-hoc in-memory maps.

## Client errors

HTTP **400** with JSON:

```json
{"status":"invalid","reason":"<code>"}
```

Reason codes: `missing_required`, `bad_content_type`, `invalid_parameter`.

## Routes

| Method | Path | Notes |
|--------|------|-------|
| GET | `/v1/catalog/items` | Query: `tenant` (required), `tags`, `filter`, `meta`, `since` |
| GET | `/v1/catalog/items/{sku}` | Path `sku`, optional `include` array |
| POST | `/v1/catalog/notes` | Header `X-Request-Id` (required), JSON body |
| GET | `/v1/admin/audit` | From admin fragment; `actor` required |

## Admission probe examples

Sample catalog probes use query values such as `tenant=acme`. Date normalization maps RFC3339 timestamps to UTC calendar days (for example `since=2024-06-15T23:30:00-07:00` becomes `2024-06-16`). `POST /v1/catalog/notes` expects a JSON body with a `text` string field. Latin-1 JSON bodies with `charset=iso-8859-1` decode to UTF-8 (for example text `café` from bytes `caf\xe9`). Unknown paths return HTTP 404 with status `not_found`.
