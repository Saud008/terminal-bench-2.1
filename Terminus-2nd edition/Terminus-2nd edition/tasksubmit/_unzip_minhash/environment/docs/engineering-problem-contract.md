# Engineering problem contract

minclus clusters near-duplicate JSONL corpus documents using MinHash signatures over normalized word shingles. Correct behavior requires NFKC token normalization, punctuation stripping, compatible permutation seeds, threshold union-find clustering, lexicographic representative selection, sketch index persistence with scan_generation, cluster graph grouping with group_generation, and provenance export with audit_digest over sorted member lists. Verifier pytest imports minhash_ref for independent reference math plus minclus_run subprocess helpers.
