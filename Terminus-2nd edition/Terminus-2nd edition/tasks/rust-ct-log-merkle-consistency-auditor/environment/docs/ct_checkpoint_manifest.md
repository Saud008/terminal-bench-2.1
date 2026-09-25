# Signed tree head and checkpoint format

Signed tree heads carry tree_size, timestamp, and sha256_root_hash as lowercase hex without prefix.

Witness checkpoints bind witness_id, log_id, tree_size, sha256_root_hash, timestamp, and opaque signature strings. Agreement is evaluated on tree_size and root hash equality for the newest head per log.
