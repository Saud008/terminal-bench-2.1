# Rule file precedence

Rule drops live under /app/fixtures/rules/stack-name/*.rules unless TB3_RULES_DIR overrides the root.

Each filename must begin with a numeric prefix, a hyphen, and a slug (example: 10-network.rules, 2-admin.rules).

Merge order uses the numeric prefix as an integer sort key ascending. When two files share the same prefix, tie-break by full filename lexicographic ascending.

Within the merged stream, later files override earlier files for the same action_id. The winning block is the last match in merged order, not the first.

Rule block syntax:

```
block
  action_id=com.example.action
  user=alice|*
  local=true|false|any
  active=true|false|any
  result=yes|no|auth_admin|auth_admin_keep|auth_self
end
```

Subject fields user, local, and active filter the block. Asterisk in user matches any username. A block matches when action_id equals the requested action and every constraint matches the subject.
