# Object store manifest format

manifest.json contains:

splits: array of objects with split_id (UUID string), parent_split_id (UUID string or null), doc_count (integer), publish_seq (integer).

lineage_root: UUID string of the oldest ancestor in the published tree.

When publishing the first split, parent_split_id is null and lineage_root equals that split_id.

When merging splits A and B into merged split M where M equals lexicographically smallest source id, parent_split_id on the new manifest row for M must be the other source split id (the lexicographically larger source), not M itself.

publish_seq increases monotonically across publish and merge operations.
