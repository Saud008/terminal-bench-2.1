# Static TTL cap schema

## static_cap_sec

Integer field on each staged renewal row. Reflects the ceiling implied by the request and the config layers below (before lifetime budget and parent delegation).

| Layer | Config / event source |
|-------|------------------------|
| requested | event `lease_ttl_sec` |
| mount | `max_lease_ttl_sec` for the event mount in `mounts.json` |
| role | `max_ttl_sec` for the event role in `roles.json` |
| policy | `policy_cap_sec` on the staged row |

Zero or negative values from any layer are fatal ingest errors. `static_cap_sec` is distinct from `granted_ttl_sec`.
