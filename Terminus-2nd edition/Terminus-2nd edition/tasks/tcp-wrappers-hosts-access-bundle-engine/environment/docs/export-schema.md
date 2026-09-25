# Export schema

## Merge export

```json
{
  "bundle": "office-edge",
  "rules": [
    {
      "index": 0,
      "side": "allow",
      "origin": "allow/10-base.allow",
      "line": 1,
      "daemons": ["sshd"],
      "clients": ["203.0.113.0/24"]
    }
  ],
  "stats": {
    "allow_rules": 1,
    "deny_rules": 0,
    "total_rules": 1
  }
}
```

## Decide export

```json
{
  "bundle": "office-edge",
  "daemon": "sshd",
  "ip": "203.0.113.10",
  "decision": "allow",
  "matched_rule_index": 0,
  "matched_side": "allow",
  "reason": "first_match"
}
```

The decide JSON object contains **only** the fields shown above (no `fingerprint`, `rules`, or other cache metadata).

When `decision` is `deny` with no rule match, set `matched_rule_index` to `-1`, `matched_side` to `""`, and `reason` to `default_deny`.

When a deny rule matches, `reason` is `first_match` and `matched_side` is `deny`.

Daemon field in decide export is the **canonical** name after alias normalization.
