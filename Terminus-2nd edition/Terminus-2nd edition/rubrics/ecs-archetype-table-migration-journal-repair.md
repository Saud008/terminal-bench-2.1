# Platform rubric — ecs-archetype-table-migration-journal-repair

**Task folder:** tasks/ecs-archetype-table-migration-journal-repair/

Agent runs archectl replay-world before migrate and writes sealed /app/state/archectl-replay-ledger.json, +3
Agent materializes /app/state/archectl-migrate-snapshot.json during replay-world with generation digest matching ledger, +3
Agent publishes migrate JSON from staged snapshot only without re-reading world fixtures, +3
Agent applies tombstone semantics so respawn journal ops cannot resurrect deleted entity ids, +2
Agent assigns component ids via seeded shuffle registration order not alphabetical names, +2
Agent splits archetype hashes when instance alignment differs across entities, +2
Agent increments sparse slot_generation on recycled entity slots, +2
Agent isolates query-batch cache keys so alpha world entities never leak into beta results, +2
Agent refreshes query cache when storage generation changes between batch steps, +2
Agent rebuilds archectl with cargo after updating archecore sources instead of editing fixture inputs or protected trap fixtures, +1
Agent patches only export wrap decoy while leaving replay ledger sealing broken, -3
Agent re-runs full world replay inside migrate instead of reading staged artifacts, -3
Agent hard-codes component_map or archetype hashes instead of deriving from journal replay, -3
Agent edits fixture inputs or protected trap fixture files to dodge replay, digest, or partial-module trap failures, -2
