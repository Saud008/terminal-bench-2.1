# Effective renewable flag schema

## effective_renewable

| Field | Type | Notes |
|-------|------|-------|
| effective_renewable | bool | Staged renewability after caller, mount, role, policy, admission, and ancestor constraints |

Related inputs appear on the renewal event (`renewable`), in `mounts.json` / `roles.json` (`renewable`), and as policy denial / admission outcomes on the staged row.
