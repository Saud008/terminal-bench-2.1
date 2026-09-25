# Segment format

Each segment is JSON at /app/data/{index}/segments/{segment_id}.json with docs (doc_id, title, body), postings map (term to sorted doc_id list), tombstones array, and field_norms map.

Title terms are lowercased tokens. Body terms are prefixed with body: before indexing. Posting checksum is a deterministic u64 over sorted term and doc_id lists defined in the CLI stats output.

Live doc count excludes any doc_id listed in tombstones.
