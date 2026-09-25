# Platform rubric — rust-minhash-dedup-corpus-clusterer

**Task folder:** tasks/rust-minhash-dedup-corpus-clusterer/

Agent applies NFKC unicode normalization before token splitting, 3
Agent strips punctuation from normalized tokens per contract charset, 2
Agent builds word shingles with exactly k consecutive tokens, 3
Agent mixes MinHash row seeds with base_seed row index and TB3_PERM_SALT, 3
Agent computes MinHash signature as minimum hash across shingles per row, 3
Agent estimates Jaccard similarity as matching signature rows divided by length, 3
Agent clusters documents when estimate meets jaccard_floor using union find, 3
Agent selects lexicographically smallest doc_id as cluster representative, 2
Agent increments scan_generation on each rescan of the same run id, 2
Agent writes audit_digest including sorted member_lists per cluster, 3
Agent rebuilds minclus after Rust source edits, 2
Agent uses scan group attest pipeline without decoy lsh telemetry module, 1
Agent uses NFC-only normalization instead of NFKC on document bodies, -3
Agent takes maximum hash instead of minimum when building MinHash rows, -3
Agent omits TB3_PERM_SALT length from permutation seed mixing, -2
Agent picks first seen doc_id instead of lexicographic minimum representative, -2
Agent leaves scan_generation unchanged after rescan of same run id, -3
