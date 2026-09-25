# Platform rubric — rust-ct-log-merkle-consistency-auditor

**Task folder:** tasks/rust-ct-log-merkle-consistency-auditor/

Agent implements RFC 6962 leaf domain byte in proof_walk before inclusion paths verify, +3
Agent requires two agreeing witness checkpoints on the active tree head, +3
Agent enforces monotonic timestamps when tree size grows across signed heads, +2
Agent walks append-only consistency audit paths to the newer Merkle root, +3
Agent materializes checkpoint rows sorted by log_id from the audit index manifest, +2
Agent seals witness_evidence_archive bundle_digest over all audit outcome rows, +3
Agent normalizes sha256_root_hash hex to lowercase before witness comparison, +2
Agent reads bundle JSON through audit_index entries rather than directory walks, +2
Agent rebuilds ctaudit via build_all.sh before subprocess pytest invocations, +1
Agent leaves stats_decoy metrics off the publish hot path, +1
Agent patches only attest_vote quorum threshold without fixing export sealing, -3
Agent fixes proof_walk alone while witness quorum still accepts one checkpoint, -3
Agent sorts checkpoint rows descending so export order diverges from contract, -2
Agent verifies inclusion against uppercase root hashes without normalize_root, -2
Agent seals archive digest from empty audit slice instead of staged rows, -3
