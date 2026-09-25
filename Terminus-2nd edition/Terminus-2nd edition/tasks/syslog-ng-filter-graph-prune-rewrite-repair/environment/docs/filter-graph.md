# Filter graph pruning

Graph routes listed in graph.conf may carry dead=1 when the route is nominally retired.

Prune removes routes when dead=1 unless the route filter_id is referenced by any rewrite rule filter_ref in rewrites.conf. Rewrite references must keep the filter alive in the pruned graph even if the graph row is marked dead.

Prune also drops routes whose filter_id is absent from filters.conf.

The pruned route list is cached under /app/state/pruned-graph.cache for reload handling.
