# OpenAPI export staging

`GET /admin/export/openapi` builds OpenAPI 3.0 from the **currently loaded** deck.

For each route operation, the `200` response `headers` map must include every header enforced by the **effective merged plugin chain** on that route:

- Headers added by `response-transformer` (`config.add.headers` as `Name:value` strings)
- `X-RateLimit-Limit` and `X-RateLimit-Remaining` when `rate-limiting` is present

Staging uses the same merge rules as runtime (`/app/docs/plugin-chain.md`). Metadata `tags` on the route are not exported as response headers unless a plugin adds them.

Export path keys use the first path entry from each route definition.
