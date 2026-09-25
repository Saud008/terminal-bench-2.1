# Evidence bundle schema

Export writes version 1 JSON with audits array sorted by log_id ascending, witness_set_hash from the first audit row, and bundle_digest sealing all audit rows.

bundle_digest hashes sorted rows containing log_id, newer_tree_size, inclusion_ok, consistency_ok, and witness_quorum_ok.
