# NSEC chain validation

Signed zones may carry NSEC records forming a linked chain across the merged zone.

## Chain rule

Collect NSEC records in final processing_order (depth-first include expansion). For each consecutive pair, the first record rdata next owner must equal the second record owner.

The chain continues across include boundaries. Do not restart validation at each fragment file boundary.

## Snapshot fields

nsec_valid is true only when no breaks exist. nsec_breaks lists objects with file, owner, expected, and got when validation fails.

## Hidden zones

The same rules apply to verifier-only trees installed under /opt/verifier-fixtures/ during image build. Tests or operators may point zonefrag at a different absolute bundle root by setting ZONEFRAG_BUNDLE_ROOT to that directory before compile or ingest.
