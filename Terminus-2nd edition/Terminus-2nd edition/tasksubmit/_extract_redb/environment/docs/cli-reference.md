# CLI reference

On this system-administration page-registry control plane, operators invoke the host-local CLI below.

Binary: /usr/local/bin/redbtool.

## batch

redbtool batch --table NAME --input PATH

Apply JSONL put/delete lines to staging. Repeated put keys in one batch keep the last value only.

## delete

redbtool delete --table NAME --key KEY

Delete one key from staging.

## commit

redbtool commit --table NAME

Run commit barrier, merge staging into committed, write btree-snapshot.json, clear staging table.

If staging has no table entry for NAME, commit is a no-op and committed data must remain unchanged.

## export

redbtool export --table NAME --out PATH

Write committed keys as JSON array of {key,value} sorted by key.

## walk

redbtool walk --table NAME

Print JSON with root_height, leaf_count, key_count, physical_entry_count, height_recorded_before_child_fsync.

## Environment

When TB3_TABLE_PREFIX is set to an absolute path, table names become PREFIX/NAME.

Evaluation may set TB3_TABLE_PREFIX to absolute roots such as /app/state/tb3_lane or /app/state/tb3_iso. Staging, commit, export, and walk must honor that prefix the same way as any other absolute staging root.
