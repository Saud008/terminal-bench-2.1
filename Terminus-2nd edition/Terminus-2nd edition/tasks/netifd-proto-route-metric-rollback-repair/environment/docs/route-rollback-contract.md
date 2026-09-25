# Route rollback contract

Route rollback runs during proto teardown after the default route is removed.

When re-installing scenario routes during rollback, use the kernel-assigned metric stored in the harness for the iface (config_metric + kernel_metric_bonus from apply). Do not reuse the bare config_metric field from the scenario JSON.

The export routes array must reflect kernel-assigned metrics after apply.
