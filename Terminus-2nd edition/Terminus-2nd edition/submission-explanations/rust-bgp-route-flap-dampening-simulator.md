# Submission explanations — rust-bgp-route-flap-dampening-simulator

**Task folder:** tasks/rust-bgp-route-flap-dampening-simulator/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-27T20:35:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `security` (offline BGP dampening admission + peer-policy integrity gates + sealed atlas/forecast attestations). Choose **Security** on the platform form. Human taxonomy may call the repair shape “debugging,” and `system-administration` is reserved for OS/service bring-up — do **not** set `debugging`, `software-engineering`, or `data-processing` (project/classifier blocked). Prefer security over system-administration when the grade is suppress/reuse trust gates on sealed emit.

## Difficulty Explanation

rdampctl admits BGP UPDATE feeds under peer dampening policy gates, replays them through a per-prefix penalty ledger, and seals a suppression atlas plus reuse-timer forecast. Rated hard because behavior is split across multiple /app/docs contracts (decay, accrual, peer tables, forecast digests, post-event stable_at_ms timing) and state files must stay consistent across compile, reapply, and publish. Partial admissions pass bundled fixtures while failing hidden TB3 cases or second-run counter rules. A decoy RIB module looks relevant but is off the hot path.

## Solution Explanation

The oracle patches the reuse-forecast path (closed-form ms_to_reuse, slot retention, anchor binding, slot_digest) and rebuilds rdampctl so emit-reuse-forecast matches /app/docs/reuse-timer-forecast.md alongside the existing suppression atlas. Follow the docs for ordering, digests, run_id gates, and the post-event stable_at_ms rule rather than patching one module in isolation.

## Verification Explanation

test.sh rebuilds the binary and runs pytest against /app/bin/rdampctl via subprocess. Reference math recomputes expected atlas and forecast rows from fixtures; static golden JSON will not pass. NOP on the broken image scores 0; oracle after patch scores 1.
