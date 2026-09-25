# Parameter authenticity trust contract

Paramgate enforces field-level trust-policy authenticity using OpenAPI 3.0 metadata from the merged spec (`/app/fixtures/openapi-base.yaml` plus `/app/fixtures/admin-paths.yaml`). Admission policy modules live under `/app/internal/bind/` (`query.go`, `explode_policy.go`, `canonical.go`, `staging.go`, `publish.go`). Legacy helpers in `wrap.go` are not on the HTTP bind hot path. After a successful authenticity bind, canonical values are staged to `/app/state/bind-snapshot.json` before the HTTP response is emitted (`/app/docs/bind-snapshot.md`).

## Query arrays (`style: form`)

| explode | Encoding | Example |
|---------|----------|---------|
| `false` | Comma-separated in one query key | `tags=alpha,beta,gamma` |
| `true` | Repeated keys | `include=stock&include=price` |

Joined array values use a **comma** delimiter when `explode` is `false`. Space-separated lists are invalid.

## Query objects (`style: deepObject`)

`deepObject` always uses bracket notation when `explode` is `true` (the default for `deepObject`):

`filter[status]=open&filter[priority]=high`

`form` style objects with `explode: false` use comma-separated `key=value` pairs in one parameter:

`meta=region=us,shard=3`

## Dates

Query parameters with `format: date` accept either `YYYY-MM-DD` or full RFC3339 timestamps. Parsed dates are normalized to the **UTC calendar day** (`YYYY-MM-DD`). Local timezone offsets must not shift the resulting day.

## Required parameters

Missing required query, path, or header parameters are client errors. The HTTP API returns status **400** with `{"status":"invalid","reason":"missing_required"}`. Status **500** is reserved for unexpected internal failures only.

## JSON request bodies

`POST /v1/catalog/notes` accepts `application/json`. When `Content-Type` includes `charset=iso-8859-1` (or `latin1`), the raw body bytes are transcoded to UTF-8 before JSON parsing. UTF-8 bodies decode without transcoding.

## Admin extension paths

Routes under `/v1/admin/` come from the admin OpenAPI fragment loaded at startup. Binding for admin query parameters follows the same style/explode rules as catalog routes.
