The turnctl CLI under /app/crates/turnctl ingests actor rosters, simulates roguelike initiative combat with bleed damage-over-time, and exports signed combat transcripts. Several paths under /app/crates/combat-core/src/ disagree with the contract docs: roster ingest validation, turn-order scheduling, bleed timing, stun action-point decrements, death pin clearing, export transcript ordering, and the simulate loop can each diverge on their own.

Repair those modules so the full ingest, simulate, and export chain matches /app/docs/normalize-contract.md and the linked docs for every scenario in /app/docs/fixture-catalog.md and every seed in /app/fixtures/seeds.json. Per-seed bleed mutation must follow /app/docs/seed-mutation.md.

Rebuild from /app, then install the release binary to /usr/local/bin/turnctl (see /app/docs/cli-reference.md). Do not edit /app/docs/, files under /app/fixtures/, or files under /tests.
