# Clone lineage contract

If any dataset (typically a filesystem) has a non-null `clone_of` value equal to a snapshot's `name`, that snapshot is blocked with reason `blocked_clone`.

Clone protection applies even when the snapshot has no holds and is not bookmarked.
