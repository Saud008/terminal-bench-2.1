# Policy revisions schema

`policies.json` maps each policy name to an ordered revision list:

```json
{
  "policies": {
    "<name>": {
      "revisions": [
        {
          "effective_from": "2026-01-01T00:00:00Z",
          "max_ttl_sec": 86400,
          "parent": "",
          "override_parent": false,
          "deny_renew": false
        }
      ]
    }
  }
}
```

## Revision record

| Field | Type | Notes |
|-------|------|-------|
| effective_from | string | RFC3339 UTC |
| max_ttl_sec | int | TTL ceiling contributed by this revision |
| parent | string | Ancestor policy name; empty when none |
| override_parent | bool | Stops further parent hops when true |
| deny_renew | bool | Marks renewals denied when encountered on a visited revision |

## Derived staging fields

| Field | Type | Notes |
|-------|------|-------|
| policy_cap_sec | int | Cap derived from the event's `policy_names` and revision trees |
| policy denied | bool | Whether any visited revision denies renewal (feeds `effective_renewable`) |

## Fatal ingest conditions

- policy name absent from `policies.json`
- no applicable revision at the event `issued_at`
- policy cycle while following `parent` links
