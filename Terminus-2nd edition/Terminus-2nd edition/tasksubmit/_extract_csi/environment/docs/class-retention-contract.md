# Storage class retention override

When a joined PVC references storage_class_name, use storage_classes retention_days for that class when retention_days is greater than zero.

When storage class retention_days is zero, fall through to backup policy and cluster default.
