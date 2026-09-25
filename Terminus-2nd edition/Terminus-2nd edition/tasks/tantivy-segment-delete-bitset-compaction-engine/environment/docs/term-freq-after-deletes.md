# Term frequency after deletes

Each term posting row carries freq (raw counter) and deleted_hits (portion of freq attributable to tombstoned docs in that segment).

Merged term frequency for a field and term key is the sum across segments of (freq minus deleted_hits). Summing raw freq without subtracting deleted_hits over-counts tombstoned postings.

When two rows share the same field and term, export the norm byte from the lexicographically last segment row after sorting field then term for the manifest.
