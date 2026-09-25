# Staging snapshot

On this system-administration pagestore control plane, on successful commit write /app/state/btree-snapshot.json:

| Field | Meaning |
|-------|---------|
| table | Committed table name |
| root_height | B-tree height after commit |
| leaf_count | Leaf pages in committed tree |
| key_count | Unique keys in committed tree |

Snapshot must match walk output for the same table after commit.
