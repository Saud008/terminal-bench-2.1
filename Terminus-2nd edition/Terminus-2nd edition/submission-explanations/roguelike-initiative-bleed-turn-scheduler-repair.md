# Submission explanations — roguelike-initiative-bleed-turn-scheduler-repair

**Task folder:** tasks/roguelike-initiative-bleed-turn-scheduler-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must align five Rust combat-core modules with seven contract docs while the broken baseline still compiles. Initiative ties, pinned-first ordering, start-of-turn bleed, stun action-point rules, death pin clearing, export ordering, and per-seed bleed mutation interact across ingest, simulate, and export. Partial fixes pass bundled catalog cases but fail hidden six-actor rosters under verifier fixtures and partial-module swap tests. Rebuild via cargo is required after every source edit.

## Solution Explanation

The oracle copies golden ingest, scheduler, bleed, export, and simulate sources from solution/files into combat-core, then runs cargo build --release for turnctl. Ingest validates negative bleed and writes staging checksums. Scheduler sorts by initiative with pinned actors first. Bleed runs at turn start. Simulate applies seed mutation then walks the corrected event order. Export hashes rounds without reordering events.

## Verification Explanation

Pytest drives turnctl through subprocess CLI calls and compares JSON exports to an independent Python reference_scheduler. Catalog scenarios run across three seeds. Hidden traps load rosters from /opt/verifier-fixtures/turnctl. Partial-fix tests swap one broken module from /opt/verifier-broken-combat while keeping golden copies elsewhere. test.sh rebuilds turnctl with cargo before pytest. Oracle reward is 1 only when all 39 tests pass.
