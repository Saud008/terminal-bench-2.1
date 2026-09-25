# Scatter planner

RouteQuery checks the cache first, then computes space via vindex hasher, then runs SimulateScatter before resolving the shard.

SimulateScatter returns Partial=true when a binary key ends with ff hex (scatter fault on shard -80). On Partial or full scatter failure, RouteQuery must not return a stale cached route. Invalidate any cache entry for that typed key and return an error. scatter_ok in the route plan is false when any query errors.

When scatter_ok is false, the route plan routes array must be empty. Do not append placeholder or error-marked route rows for failed queries; failure counts belong in routing-audit.json scatter_failures per export-schema.md.

Successful scatter stores the computed shard with the current shard map generation.
