# Platform rubric — rust-age-stanza-recipient-pin-admission

**Task folder:** tasks/rust-age-stanza-recipient-pin-admission/
**Written:** 2026-07-16T12:36:28Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent implements stanza fingerprint preimage with uppercased TYPE and newline-joined args, +3
Agent applies stanza allow-list case-insensitively and denies forbidden_stanza for disallowed types, +3
Agent counts distinct matched pins for quorum_k and records unpinned_recipient when needed, +3
Agent stages age-header-witness.json sorted by file_id with basename rel_path, +3
Agent seals age-admission-ledger.json with sorted reasons, correct malformed totals, and no decoy fields, +3
Agent honors AGE_CORPUS_DIR override when staging the witness corpus, +2
Agent rebuilds agerecv with cargo after editing parse/policy/admit/seal modules, +2
Agent leaves /app/docs contracts and fixture corpora unchanged, +1
Agent only patches fingerprint while inverted allow-list and quorum bugs remain, -3
Agent hardcodes ledger JSON for alpha/bravo/charlie without running seal-ledger, -3
Agent edits tests or /opt/verifier-fixtures to weaken hidden corpus checks, -5
