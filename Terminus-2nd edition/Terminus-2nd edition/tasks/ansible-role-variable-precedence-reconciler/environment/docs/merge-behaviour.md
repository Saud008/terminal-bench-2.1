# Hash merge behaviour

When `hash_behaviour` is `merge`, dictionary values combine recursively:

```yaml
base:
  cache:
    enabled: true
    ttl: 60
overlay:
  cache:
    ttl: 10
```

Result:

```yaml
cache:
  enabled: true
  ttl: 10
```

With `replace`, the entire `cache` key from the overlay replaces the base mapping.

`include_vars` depth ordering is independent from hash behaviour: shallower depths apply before deeper depths, and deeper mappings still participate in recursive merge when enabled.
