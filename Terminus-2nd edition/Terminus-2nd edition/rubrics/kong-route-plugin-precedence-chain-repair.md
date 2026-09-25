# Platform rubric — kong-route-plugin-precedence-chain-repair

**Task folder:** tasks/kong-route-plugin-precedence-chain-repair/

# Rubric 1

Agent validates deck plugins and route references before mutating the in-memory store, +3
Agent returns routes_loaded zero on HTTP 422 ingest failures, +3
Agent applies longest path prefix with method gate at that length without shorter fallback, +3
Agent returns HTTP 404 when longest prefix route fails method check, +2
Agent sets X-Matched-Route to chosen route name on matched proxy 200 responses, +2
Agent merges service and route response-transformer add.headers additively, +3
Agent keeps distinct service plugin names when route overlays same plugin family, +3
Agent runs rate-limiting before response-transformer in access chain, +3
Agent omits response-transformer headers on HTTP 429 rate-limit blocks, +2
Agent authorizes JWT using route scope_tags not metadata tags field, +3
Agent exports OpenAPI operations with merged plugin-enforced response headers, +3
Agent reads staged plugin headers from merged chain not route-only config, +3
Agent returns HTTP 401 when consumer scopes lack required scope_tags, +2
Agent writes partial route rows during ingest validation loop, -3
Agent replaces entire service plugin list when route declares overlapping plugin name, -3
Agent treats route metadata tags as JWT scope requirements, -3
