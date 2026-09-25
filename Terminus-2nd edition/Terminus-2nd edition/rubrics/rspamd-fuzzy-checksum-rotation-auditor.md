# Platform rubric — rspamd-fuzzy-checksum-rotation-auditor

**Task folder:** tasks/rspamd-fuzzy-checksum-rotation-auditor/

Agent implements rotate pipeline writing shingle snapshot before sqlite mutation, +3
Agent normalizes mail bodies to lowercase collapsed whitespace before shingle emission, +2
Agent emits window-sized shingles with correct hash digest prefix for key epoch and algorithm, +3
Agent rotates seeded fuzzy_hashes rows to new epoch and algorithm via rehash not metadata-only update, +3
Agent counts unique_shingles with distinct hash semantics separate from total_shingle_rows, +3
Agent verifies console dump lines against index using lowercase hash comparison, +2
Agent writes rotation-run.json on success mirroring summary counters plus completed_at, +2
Agent writes rotation-rollback.json with console_mismatch reason on verify failure, +2
Agent honors dry-run skipping sqlite inserts and rotation-run while still emitting summary, +2
Agent lists shingle snapshot mails in mails.tsv order excluding stray corpus eml files, +3
Agent applies RF_EPOCH_SALT_SUFFIX when computing epoch_salt in snapshot digest, +2
Agent fixes only body extraction while leaving window size off-by-one in shingles awk, -3
Agent patches decoy wrap module onto rotate hot path instead of summary rollup, -3
Agent counts unique_shingles as total shingle rows ignoring duplicate hashes across mails, -5
Agent skips rollback marker when console verification fails after index mutation, -3
Agent includes sorted glob eml stems in snapshot instead of manifest mail_id sequence, -2
