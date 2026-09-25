# Commit barrier

On this system-administration pagestore control plane, during commit the storage engine must persist child page payloads before the commit record reflects final root height.

1. Flush all child page payloads to /app/state/pages.json (fsync simulation).
2. Write /app/state/commit_record.json with root_height and children_fsynced true.
3. Never record root_height while children_fsynced is false on the final record.

The field height_recorded_before_child_fsync must remain false after a successful commit.
