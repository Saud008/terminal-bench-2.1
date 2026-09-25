# Config reload and hash cache

The driver stores config hash at /app/state/config.hash and pruned graph cache at /app/state/pruned-graph.cache.

--reload full always recomputes hash from filters.conf, graph.conf, and rewrites.conf and rebuilds pruned graph.

--reload partial recomputes hash when any of those three files change since the last replay; partial reload must invalidate cache when configuration content changes even if the messages path is unchanged.

When cache is valid, replay reuses pruned-graph.cache. When invalidated, replay must rebuild prune output before routing.
