# Plugin merge and chain order

## Merge (`internal/merge`)

Effective plugins for a request combine **service** and **route** plugin lists:

- Start with service-level plugins in declaration order.
- Overlay route-level plugins; when the same plugin `name` appears at both levels, merge that plugin's configuration (see below).
- Both levels contribute distinct plugin names (e.g. service `response-transformer` + route `rate-limiting` both apply).

### Same plugin name at service and route

When service and route both declare the same plugin `name`:

- **Distinct plugin names** — each level keeps its own entry (service `rate-limiting` + route `jwt` both run).
- **`response-transformer`** — merge `config.add.headers` additively, not wholesale replacement:
  - Start from service `add.headers`, then overlay route `add.headers`.
  - For the same header name, the **route** value wins.
  - Headers present only on the service (for example `X-Service-Layer`) must still appear alongside route-only headers (for example `X-Route-Layer`).
- **Other shared names** — route `config` replaces service `config` for that plugin name.

## Execution order (`internal/chain`)

Access-phase plugins run before response-phase plugins:

1. `jwt` (access — may return 401)
2. `rate-limiting` (access — may return 429)
3. `response-transformer` (response/header filter)

When rate limiting blocks a request, response-transform headers must **not** appear on the 429 response.

Rate-limit counters are keyed by `route name` + `X-Api-Key` header (empty string if absent).
