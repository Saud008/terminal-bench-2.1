# Dead branch and fallback flags

Each graph route has fallback (0 or 1). When fallback=1 the route is a fallback path and must never be removed during dead-branch pruning even when dead=1.

Routes with fallback=0 and dead=1 are removed unless protected by rewrite reference rules in filter-graph.md.

The pruned graph must preserve the original graph.conf file order for every retained route. Do not sort routes by route_id or any other field.
