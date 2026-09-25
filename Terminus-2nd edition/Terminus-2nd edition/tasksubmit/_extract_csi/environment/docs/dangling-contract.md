# Dangling snapshot contract

A VolumeSnapshot is dangling when no PVC exists with matching namespace and source_pvc name.

orphan-snapshot-ledger.jsonl rows: uid, namespace, source_pvc, kind=dangling.

Rows sort by uid ascending then namespace ascending. File ends with trailing newline when non-empty.
