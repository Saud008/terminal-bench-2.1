# Platform rubric — party-invite-audit-staging-governor

**Task folder:** tasks/party-invite-audit-staging-governor/

Agent implements canonical staging digest encoding per staging-digest.md, +3
Agent implements chained ledger append with party-scoped suppression and retention, +3
Agent stages lifecycle mutations into the audit ledger via WriteAuditSnapshot, +3
Agent verifies the ledger chain and seals export occupancy from the staged entry, +3
Agent advances sweep_epoch before refresh and retires vanished parties, +3
Agent reconciles reserved_slots across staged pending and live connected invitees, +2
Agent persists audit_seq, party_seqs, and sweep_epoch across daemon restarts, +2
Agent refuses export with the documented tokens without writing the output file, +2
Agent rebuilds partyd after editing governor modules, +2
Agent ignores LegacyCapGuard and LegacySealDigest for ledger digests and occupancy, +1
Agent implements only publish math while ingest staging writes remain no-ops, -3
Agent fixes sweeper without epoch bump or snapshot refresh after expiry, -3
Agent derives effective occupancy from SQLite invite counts while the ledger exists, -3
Agent suppresses against the ledger tail instead of the party's newest retained entry, -2
Agent uses LegacySealDigest or wall-clock time for entry digests, -2
