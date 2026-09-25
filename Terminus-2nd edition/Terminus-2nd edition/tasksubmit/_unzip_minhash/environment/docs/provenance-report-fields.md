# Provenance report fields

Dedup eval reports are written under /app/output/ minclus attest writes a dedup eval report JSON with run_id, cluster_run_id, jaccard_floor, total_documents, cluster_count, singleton_count, clusters array, and audit_digest. Default bundled output path is /app/output/<run-id>-provenance.json using the -provenance.json suffix pattern.

Clusters export sorted by cluster_id ascending. Each cluster includes cluster_id, representative_doc_id, member_doc_ids sorted ascending, source_paths aligned to member order, and min_pairwise_estimate.

singleton_count counts clusters whose member_doc_ids length equals one.

audit_digest is SHA256 hex of JSON with keys cluster_count, cluster_run_id, jaccard_floor, member_lists, run_id, singleton_count, total_documents. member_lists is an array of sorted member_doc_ids arrays ordered by cluster_id. Use compact JSON with sorted keys and no spaces.
