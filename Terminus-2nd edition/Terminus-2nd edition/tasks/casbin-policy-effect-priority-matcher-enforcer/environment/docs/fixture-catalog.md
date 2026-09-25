# Fixture catalog

Offline policy admission fixtures for casctl trust-gate verification.

| Path | Purpose |
|------|---------|
| `fixtures/models/rbac_domains_priority.conf` | Domain policy model with priority and deny effect |
| `fixtures/policies/bundle-a/` | Tenant1 base rules (16 policies) |
| `fixtures/policies/bundle-b/` | Tenant2 base rules (12 policies) |
| `fixtures/policies/bundle-c/` | Cross-tenant ticket/shared rules (7 policies) |
| `fixtures/requests/batch-alpha.jsonl` | Tenant1 scenarios |
| `fixtures/requests/batch-beta.jsonl` | Tenant2 inheritance and domain isolation |
| `fixtures/requests/batch-gamma.jsonl` | Bundle-c ticket/shared overlap cases |

Config `seed` selects and orders bundle subsets loaded for each enforcement run.
