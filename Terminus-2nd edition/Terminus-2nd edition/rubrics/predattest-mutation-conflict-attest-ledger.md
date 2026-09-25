# Platform rubric — predattest-mutation-conflict-attest-ledger

**Task folder:** tasks/predattest-mutation-conflict-attest-ledger/
**Written:** 2026-07-17T20:38:48Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent stages /app/state/wavehold/hold-witness.json during compile before the atlas is published, +3
Agent publishes /app/output/mutation-rollout-atlas.json with a 64-hex atlas_digest over outcomes, nodes, and schema_marks, +3
Agent holds only exact deny-pin attrs and lets near-miss attrs like drain_token_scope pass through, +3
Agent binds a blank upsert only when every bind_on key matches by value and by sorted-facet keys, +3
Agent picks conflicting scalar winners by highest edit_rank then later record index, never wall_time_ms, +3
Agent keeps list entries distinct on the (value, lang) pair in insert order, +2
Agent evaluates every @if precondition against the live fleet-graph state before any write in the record, +2
Agent rolls the graph and schema-mark snapshot back when a record has commit false, +2
Agent implements one decision per gate module under /app/lib/wavehold/gates and leaves the decoy wall-time helper unused, +2
Agent leaves /app/docs, /app/fixtures, and /app/config/wavehold.json unchanged, +1
Agent fixes only one gate module while the other gates stay wrong, -3
Agent lets wall_time_ms decide conflicting scalar winners, -3
Agent edits protected fixtures or the verifier math under /tests to force a pass, -5
