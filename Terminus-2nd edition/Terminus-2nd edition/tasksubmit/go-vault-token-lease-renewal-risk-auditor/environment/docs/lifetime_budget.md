# Token lifetime budget schema

Lifetime fields are relative to the token's origin renewal (lowest `renewal_seq` for that `token_id` in the corpus).

## Config

`mounts.json` and `roles.json` entries include `max_token_lifetime_sec` beside lease caps:

```json
{"mounts": {"<name>": {"max_lease_ttl_sec": 43200, "max_token_lifetime_sec": 10800, "renewable": true}}}
{"roles":  {"<name>": {"mount": "<name>", "max_ttl_sec": 7200, "max_token_lifetime_sec": 10800, "renewable": true}}}
```

## Staged fields

| Field | Type | Notes |
|-------|------|-------|
| lifetime_ceiling_sec | int | Ceiling drawn from the event's mount and role lifetime settings |
| budget_remaining_sec | int | Non-negative remaining lifetime budget for this renewal |

A lifetime ceiling of zero or below is a fatal ingest error.
