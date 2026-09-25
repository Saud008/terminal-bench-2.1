# Tenant quota policy

max_active per tenant is quotas.json tenants.TENANT_ID.max_active adjusted by TB3_QUOTA_BIAS (added, floored at zero).

Quota accounting counts only ledger rows with status active after expiry eviction runs.

When active rows exceed max_active after expiry, evict active rows with the smallest last_seen_ms until active count equals max_active. Tie-break by operation_id lexicographic ascending.

quota_headroom in reconcile-report.json is max(0, max_active - active_count) after eviction.

Reconcile report quota_max is the effective max_active after bias.
