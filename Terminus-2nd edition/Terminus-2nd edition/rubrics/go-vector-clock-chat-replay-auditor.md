# Platform rubric — go-vector-clock-chat-replay-auditor

**Task folder:** tasks/go-vector-clock-chat-replay-auditor/

Agent loads numbered shard_NNN.jsonl files in numeric order into chat-staging.json with staging_digest, +3
Agent reconciles causally sorted events and emits clock_drift when increment(frontier, sender) differs from event vector_clock, +3
Agent flags moderation_conflict when concurrent moderation actions target the same user with different ranks, +2
Agent applies half-open mute intervals and emits mute_leak only for messages inside active mute windows, +2
Agent validates delivery receipts with happens-before rules and flags receipt_mismatch on invalid proofs, +2
Agent suppresses duplicate_delivery on the lexicographically larger receipt id for same ref and recipient, +2
Agent detects clock_gap when adjacent causal clocks exceed max_gap including TB3_GAP_BIAS offset, +2
Agent emits timeline rows only after reconcile_revision is greater than zero with sealed timeline_digest, +2
Agent rebuilds vcreplay with verifier-rebuild.sh after editing Go sources before pytest, +1
Agent patches only clockjump gap detection while leaving frontier clock_drift reconcile broken, -3
Agent hard-codes reconcile findings instead of walking causal frontier per gap-findings-contract.md, -3
Agent consults decoy fork_alias module on ingest or export hot path, -2
Agent weakens hidden TB3 gap-trap or precedence-trap fixture coverage, -2
Agent emits timeline before reconcile increments reconcile_revision barrier, -3
