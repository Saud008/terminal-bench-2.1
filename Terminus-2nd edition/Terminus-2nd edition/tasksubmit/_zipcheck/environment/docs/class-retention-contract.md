# Storage class retention override

Storage class retention applies only after backup policy resolution fails (see policy-precedence-contract.md).

When no matching backup_policies row applies and a joined PVC references storage_class_name, use that storage class retention_days when retention_days is greater than zero.

When storage class retention_days is zero, or the snapshot PVC is unresolved, fall through to cluster default_retention_days (or TB3_CLUSTER_DEFAULT_RETENTION_DAYS, or 30 days).
