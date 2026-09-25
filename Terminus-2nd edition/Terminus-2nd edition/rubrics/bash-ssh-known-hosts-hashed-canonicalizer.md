# Platform rubric — bash-ssh-known-hosts-hashed-canonicalizer

**Task folder:** tasks/bash-ssh-known-hosts-hashed-canonicalizer/

Agent writes JSONL staging ledger rows with monotonic seq starting at one, +3
Agent seals manifest input_sha256 from raw input bytes not basename, +3
Agent verifies ledger_sha256 and record_count before export proceeds, +3
Agent parses @revoked marker before @cert-authority without lowercasing host tokens, +3
Agent preserves hashed |1|salt|hash segments case-sensitively end to end, +3
Agent normalizes bracket ports as [host]:port with inner hostname lowercased only, +2
Agent merges duplicate keys preferring non-revoked then greatest comment, +2
Agent sorts plain before hashed then host_sort_key port key_type revoked_flag, +2
Agent emits @revoked and @cert-authority markers from export module not merge only, +2
Agent ignores decoy kh_sort_legacy key-blob ordering off export hot path, +1
Agent patches only decoy sort helper while leaving merge sort tuple broken, -3
Agent fixes parse bracket shape but keeps bracket token as plain host_sort_key, -3
Agent writes ledger to sidecar raw file instead of kh-ledger.jsonl contract, -2
Agent hashes manifest input from filename instead of file bytes, -2
Agent drops hashed line comments in export emit layer, -2
