# Export plan schema

Path default: /app/output/device_plan.json

## Schema

```
{
  "schema_version": 1,
  "devices": [
    {
      "dev_id": "...",
      "symlinks": ["sorted unique names"],
      "owner": "string or null",
      "group": "string or null",
      "mode": "four digit octal or null",
      "winning_rules": ["rule_id..."]
    }
  ],
  "collisions": [
    {
      "symlink": "name",
      "candidates": ["rule_id..."],
      "winner": "rule_id"
    }
  ],
  "plan_digest": "64 lowercase hex"
}
```

Devices sorted by dev_id. symlinks sorted lexicographically.

## Symlink collisions

When multiple matching rules emit the same symlink name for one device, the winner is the rule latest in effective order among candidates. Record every collision where two or more rules contributed the same symlink.

## Permission precedence

Scan matching rules for a device from latest to earliest effective order. For each field independently, take the last non-empty OWNER, GROUP, or MODE token. If still empty after scan, use policy defaults from POLICY_JSON (default_owner, default_group, default_mode).

MODE must be four digit octal with leading zeros.

## plan_digest

SHA-256 hex of lines built from devices sorted by dev_id:

dev_id|comma symlinks|owner|group|mode|comma winning_rules

One device per line, newline joined.

Export must consume match_edges and rules from the staging file only.
