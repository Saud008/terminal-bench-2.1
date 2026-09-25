# Witness quorum policy

For each log_id the newest tree head must be attested by at least two independent witnesses sharing the same tree_size and sha256_root_hash.

witness_set_hash is a stable fingerprint over sorted agreeing witness_id values for that head.
