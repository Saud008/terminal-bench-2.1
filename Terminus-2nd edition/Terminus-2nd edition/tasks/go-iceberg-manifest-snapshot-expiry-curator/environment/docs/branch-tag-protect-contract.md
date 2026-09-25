# Branch and tag protection

Each ref in table.refs pins a snapshot_id for a branch or tag name.

Protected snapshots include every ancestor of each ref snapshot per snapshot-ancestry-contract.md.

Expiry planning must never mark protected snapshots as expired.
