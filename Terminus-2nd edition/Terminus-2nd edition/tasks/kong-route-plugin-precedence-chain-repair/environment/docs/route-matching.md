# Route matching

`internal/match` selects a route for `(method, path)` from the loaded deck.

Rules:

1. **Longest path prefix** — find the maximum prefix length among all routes whose `paths` entry is a prefix of the request path. Routes whose path does not prefix-match contribute length **zero** and are not candidates at this step.
2. **Method filter at that prefix** — among routes whose prefix length equals that maximum, keep only routes whose `methods` list includes the request verb (case-insensitive). An empty `methods` list matches any verb.
3. **No match** — if no route satisfies both rules, the proxy returns **404** (not 405). When a longer prefix matches the path but no route at that prefix allows the verb, do **not** fall back to a shorter-prefix route with a matching method.

Example: `GET /api/v2/catalog/items/special` must return **404** when the longest matching prefix is a `POST`-only route on `/api/v2/catalog/items/special`, even if a shorter `GET` route exists on `/api/v2/catalog`.

Matching is used by the proxy before plugin execution.

## Matched route header

On a successful proxy match (HTTP 200 before plugin blocks), the response must include **`X-Matched-Route`** set to the chosen route's `name` field. Verifiers use this header to confirm longest-prefix and method selection without parsing upstream bodies.
