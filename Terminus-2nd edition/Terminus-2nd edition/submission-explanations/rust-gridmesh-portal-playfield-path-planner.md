# Submission explanations - rust-gridmesh-portal-playfield-path-planner

**Task folder:** tasks/rust-gridmesh-portal-playfield-path-planner/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-21T16:30:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `games` (portal playfield path puzzle / tactics board playtest / seeded jump scoring / sealed validate+path win-condition exports). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` under short closure framing and `start with` docs order; keep the playfield-puzzle / playtest-win-condition framing and the explicit “not a Rust CLI / navmesh rebuild exercise” negation.

## Difficulty Explanation

Marked hard because cost, link, and validate playtest rules span several board scenarios so a partial change can look fine on one mesh while portal snap or island checks still fail elsewhere.

## Solution Explanation

The oracle drops corrected cost, link, and validate libraries into the app tree, rebuilds navmeshctl, and drives validate and path against the same board fixtures agents see. Exports must follow the games playtest contracts for Q16 totals, bidirectional links, and linear snap instead of hard coding one board.

## Verification Explanation

Pytest drives navmeshctl via subprocess and recomputes expected JSON from an independent reference so pasted goldens cannot pass. NOP on the baseline should score zero and the oracle libraries should clear the suite.
