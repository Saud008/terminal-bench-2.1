# ML eval metrics contract

minclus treats each document as a sparse feature embedding approximated by a MinHash signature vector. Pairwise similarity eval uses the fraction of matching signature rows between two documents.

## Jaccard eval metric

Given signatures of length n, count positions where values match. The Jaccard estimate equals matching divided by n as a floating-point metric in zero to one.

## Batch clustering threshold

During group, connect two documents when their Jaccard estimate is greater than or equal to jaccard_floor. Union-find merges connected components into clusters. Each multi-member cluster records min_pairwise_estimate as the minimum pairwise metric among members.

## Dedup eval report fields

The attest export includes total_documents, cluster_count, singleton_count, and per-cluster member lists. singleton_count counts clusters with exactly one member. audit_digest seals the eval summary for reproducible training-batch dedup attestation.

## Profile presets

Profiles named default, strict, and relaxed in /app/fixtures/run_profiles.json supply jaccard_floor presets for batch eval. scan records the active profile name in the sketch index.
