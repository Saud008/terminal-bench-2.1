# Submission explanations — library-hold-queue-fairness-reconciler

**Task folder:** tasks/library-hold-queue-fairness-reconciler/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a multi-stage holdfairctl pipeline where SQLite scenario state, on-disk staging fingerprints, suspension calendars, branch pickup rules, and priority tiers all interact. Fixing copy routing alone leaves staging digest drift, wrong run stamps, or atlas rows sorted by copy id instead of queue position. Hidden traps use inclusive suspension boundary dates and decoy on_shelf copies that look available to naive selectors. Partial fixes pass bundled clean scenarios but fail TB3 overlays unless every contract layer aligns.

## Solution Explanation

The oracle patches six Go modules covering suspension bounds, tier sort order, copy selection with interbranch fallback, stable staging digest ordering, scenario-aware idempotency stamps, and atlas publish sorting. It updates reconcile to pass the scenario into the stamp helper, rebuilds holdfairctl offline, and runs the four verb pipeline against seeded SQLite fixtures built by build_scenarios.py.

## Verification Explanation

Pytest drives holdfairctl through subprocess calls and compares outputs to an independent hold_queue_refmath simulator that reads the same SQLite files. Tests cover staging digests, assignment rows, suspension blocks, tier precedence, branch routing, idempotent rerun stamps, and TB3 hidden fixtures under /opt/verifier-fixtures/holdfairctl with optional reconcile date overrides.
