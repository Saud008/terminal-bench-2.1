# Merge and commit order

When merging staging segments, doc_id offsets from later segments must be added to every posting list before postings are combined. Tombstone doc_ids receive the same offset as their source segment.

After the merged segment is written, obsolete staging segment ids must be removed from reader_registry before the merged segment id is registered as committed. dangling_reader_count counts obsolete ids still present in reader_registry.

Merge finalize sets pending_live_docs using live doc count after tombstones are applied to the merged segment docs.
