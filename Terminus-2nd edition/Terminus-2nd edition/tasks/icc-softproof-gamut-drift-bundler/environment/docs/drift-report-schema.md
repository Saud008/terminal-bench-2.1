# Drift report schema

Schema: icc-drift-report/1

Written only by export from staging evaluation block.

| Field | Type |
|-------|------|
| schema | string |
| readings_digest | string |
| profile_digest | string |
| policy_digest | string |
| profile_id | string |
| evaluated_as_of | integer |
| summary | object |
| patches | array |

summary fields: patch_count, drift_count, checksum_fail_count, ticket_invalid_count, delta_e_drift_count

patches copies evaluation per_patch sorted by patch_id.

JSON keys sorted with indent 2 and trailing newline.

export exit code 2 when summary.drift_count is greater than zero.
