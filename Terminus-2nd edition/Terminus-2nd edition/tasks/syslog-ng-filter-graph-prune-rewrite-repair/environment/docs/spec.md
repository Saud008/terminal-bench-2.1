# Syslog-ng replay specification

The replay driver loads three configuration files from the config directory:

- filters.conf — filter_id|boolean_expression
- graph.conf — route_id|filter_id|destination|fallback|dead
- rewrites.conf — rewrite_id|filter_ref|template

Messages are comma-separated lines: msg_id,facility,level,program,host,text

Processing order for each message:

1. Load and optionally cache the pruned active graph (see reload-cache.md).
2. Apply facility gate filters before any rewrite (rewrite-order.md).
3. Apply rewrite templates for matching filter_ref entries (rewrite-order.md).
4. Evaluate each active graph route boolean filter; deliver to destination on match.
5. Write routing-snapshot.json then export report JSON.

Pruning runs at load time and must retain nodes referenced by rewrites even when marked dead in graph.conf (filter-graph.md). Dead-branch removal must keep fallback routes (branch-fallback.md).

Boolean expressions support facility(name), level(name), program(name), &&, ||, and parentheses. AND binds tighter than OR (boolean-precedence.md).
