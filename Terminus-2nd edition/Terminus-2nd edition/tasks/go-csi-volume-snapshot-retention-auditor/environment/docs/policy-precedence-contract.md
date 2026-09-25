# Deletion policy precedence

Operational fleet retention rules resolve in order:

1. snapshot deletion_policy Retain blocks automatic expiry regardless of other rules.
2. Highest priority backup_policies row matching snapshot namespace via namespace_selector or empty selector.
3. storage class retention_days when joined PVC class override is greater than zero.
4. cluster default_retention_days or TB3_CLUSTER_DEFAULT_RETENTION_DAYS or 30 days.

A snapshot is deletable when age in whole days from audit_clock_ms meets or exceeds resolved retention days and it is not Retain protected. Deploy-time backup policy priority governs rollout retention within each namespace.
