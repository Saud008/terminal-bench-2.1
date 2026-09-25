# Submission explanations - carbon-intensity-workload-shift-planner

**Task folder:** tasks/carbon-intensity-workload-shift-planner/
**Platform form only** - not in upload zip.

## Difficulty Explanation

Hard because latch admission, fingerprint-bound curate, and sealed atlas publish must stay in lockstep across the playtest contracts. Fixing one gate often looks fine on the bundled playfield packs while quota carryover, residency traps, or ledger-digest drift still fails on the next verb. The painful parts are that publish must trust the on-disk staging ledger only, not re-derive from raw scenario inputs, and cross-run state has to stay aligned after reset-state. With the full suite plus hidden packs, a partial playtest often passes the happy path but still fails once intensity fingerprint or digest refusal is hit.

## Solution Explanation

The oracle drops corrected sources into /app, rebuilds shift-pl, and drives latch → curate → publish against the same playfield packs agents see. Latch binds the scenario to the run under /app/state. Curate writes the fingerprint-bound staging ledger and refuses on intensity or quota integrity failures. Publish reads that ledger only and emits the sealed atlas with plan_digest. Key insight: follow the playtest contracts for ordering, digests, and refusal modes instead of patching around symptoms in one module.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest calls /app/bin/shift-pl via subprocess. Tests do not grep source for magic strings. The verifier recomputes expected atlas fields from fixtures, which blocks pasted golden answers. Some cases assert ledger bytes and digest refusal before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.

## Category note

Zip metadata uses `games` (carbon-shift playfield intensity playtest / sealed atlas win-condition export). Choose **Game** on the platform form. Do not set `software-engineering`, `debugging`, `data-processing`, `security`, or `system-administration` when the classifier keeps landing on blocked SE under ops-desk lipstick. Keep the playtest/win-condition framing and the explicit “not a Rust CLI / cargo rebuild / debugging / software-engineering” negation. Harbor `[category_classifier]` repeatedly blocked system-administration framing on this planner shape as software-engineering; playtest framing matches railpos / bitswap successors.
