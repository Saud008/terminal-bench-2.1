# Lineage graph contract

Lineage edges are directed from from_officer_id to to_officer_id ordered by event_epoch_ms ascending per evidence_id.

The first transfer for an evidence item anchors from_officer_id as collection_officer. Missing intermediate custody hops emit lineage_gap.
