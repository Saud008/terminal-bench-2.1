# Version ledger export

migratectl export writes /app/output/version-ledger.json with fields max_version, dirty, failed_down_rollbacks, stage_version, and export_pass.

max_version is the integer maximum of all rows in version_log, not lexicographic string order.

Export must open schema_migrations under BEGIN EXCLUSIVE so concurrent apply cannot mutate version_log during export.

failed_down_rollbacks is copied from the stage snapshot.
