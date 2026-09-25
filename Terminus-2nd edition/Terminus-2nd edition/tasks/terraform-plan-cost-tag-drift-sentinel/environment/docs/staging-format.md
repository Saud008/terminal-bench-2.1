# Staging format

Path default: /app/state/plan-tag.stage

Schema: plan-tag-stage/1

| Field | Type | Description |
|-------|------|-------------|
| schema | string | Always plan-tag-stage/1 |
| plan_digest | string | sha256 hex of canonical plan JSON bytes |
| policy_digest | string | sha256 hex of canonical policy JSON bytes |
| evaluated_on | string | Copied from policy evaluated_on |
| resources | array | Normalized resource rows |

Each resource row:

| Field | Type | Description |
|-------|------|-------------|
| address | string | Resource address |
| previous_address | string or null | Set when moved |
| actions | array | change.actions |
| provider_key | string | From plan |
| provider_scope | string | After alias resolution |
| effective_tags_before | object | Canonical key to string value |
| effective_tags_after | object | Canonical key to string value |
| unknown_keys_after | array | Canonical keys unknown after apply |
| moved | boolean | True when move in actions |

Resources sorted by address ascending before write.
