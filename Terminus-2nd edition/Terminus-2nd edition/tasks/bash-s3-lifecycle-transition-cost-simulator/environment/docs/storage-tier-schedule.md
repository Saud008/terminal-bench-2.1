# Storage tier schedule

Age in days for a version at simulation date D is floor((D - last_modified_date) in whole days).

Tier moves apply when age **>=** transition.days. Multiple transitions in one rule apply in ascending days order; each move updates storage_class for charge simulation at window_end.

Expiration removes the version from billable inventory when age >= expiration.days unless a billing freeze applies.

noncurrent_expiration applies only to versions that are not the current version for the key at window_end. Age for noncurrent versions uses days since the version became noncurrent (when a newer version or delete marker was recorded).
