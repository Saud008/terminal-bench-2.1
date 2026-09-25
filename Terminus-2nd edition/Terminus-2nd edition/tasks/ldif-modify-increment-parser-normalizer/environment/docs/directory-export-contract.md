# Directory export contract

Written by ldif-apply apply --export.

Top-level object:

| field | type | notes |
|-------|------|-------|
| seed | string | same as --seed |
| stats | object | see below |
| entries | array | final directory snapshot |

stats:

| field | meaning |
|-------|---------|
| records_total | change records parsed from the file |
| records_applied | records that changed the directory |
| records_skipped | records not applied (malformed, or modify when the DN is missing) |

Each entry in entries:

| field | meaning |
|-------|---------|
| dn | distinguished name |
| attributes | map of lowercase attribute name to sorted list of values |

entries is sorted by dn ascending. Values within each attribute list are sorted lexicographically.
