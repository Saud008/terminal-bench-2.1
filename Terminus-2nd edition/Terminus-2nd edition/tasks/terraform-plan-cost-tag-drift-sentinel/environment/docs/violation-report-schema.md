# Violation report schema

Path default: /app/output/tag-violations.json

Schema: tag-violation-report/1

| Field | Type | Description |
|-------|------|-------------|
| schema | string | Always tag-violation-report/1 |
| plan_digest | string | From staging |
| policy_digest | string | From staging |
| violations | array | Sorted rows (see below) |
| waived | array | Waiver applications |
| summary | object | Counts |

## Violation row

| Field | Type | Description |
|-------|------|-------------|
| code | string | MISSING_REQUIRED_TAG, TAG_DRIFT_REMOVE, or UNKNOWN_EXEMPT |
| severity | string | deny for violations; info for UNKNOWN_EXEMPT |
| resource | string | Resource address |
| tag_key | string | Canonical key |
| rule_id | string | Deny rule id or empty for drift or unknown |
| message | string | Human-readable summary |

Sort violations by (resource, tag_key, code) lexicographically.

## Waived row

| Field | Type | Description |
|-------|------|-------------|
| waiver_id | string | From policy |
| resource | string | Resource address |
| tag_key | string | Canonical key |

## Summary

| Field | Type | Description |
|-------|------|-------------|
| deny_count | integer | Violations with severity deny |
| waived_count | integer | Length of waived array |
| unknown_exempt_count | integer | Violations with code UNKNOWN_EXEMPT |

audit exit code 2 when deny_count is greater than zero.
