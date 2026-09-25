# Protocol latch schema

compile-trial writes /app/state/trial-latch.json with trial_id, protocol_version, arms, block_sizes, strata list, protocol_digest, and log_relpath. protocol_digest is sha256 hex of a canonical JSON preimage containing trial_id, protocol_version, sorted arms, block_sizes, seed_salt, and each stratum_id with sorted factor JSON.
