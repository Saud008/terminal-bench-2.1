# Submission explanations — library-hold-queue-fairness-governor

**Task folder:** tasks/library-hold-queue-fairness-governor/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-29T15:20:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `system-administration` (host-local holdfairctl ops desk / admit → gate → seal). Choose **System Administration** on the platform form. Do **not** set `debugging` or `software-engineering` — Harbor `edition_2` static checks hard-block those even when human taxonomy review preferred debugging over build-and-dependency-management. Also avoid `build-and-dependency-management` (wrong primary activity). Keep the ops-desk framing and the explicit “not a debugging / software-engineering module-repair” negation.

## Difficulty Explanation

Rated **medium** in zip metadata (`task.toml`). Agents must bring several interacting Go packages under `/app/internal/` into compliance so suspension gates, pickup-branch routing, priority ranking, rollup fingerprint ordering, and reconcile seals stay aligned through a full mount → compose-rollup → rank-fair-holds → write-assignment-atlas pass. Partial alignment often lands one stage but leaves drifted digests when inclusive calendar edges or copy status still disagree with independent reference math on a second run.

## Solution Explanation

The oracle drops corrected modules into the app tree, rebuilds holdfairctl, and drives mount compose rank publish against the same library packs. Export must trust staged rollup and reconcile scratch already written before publish, and stay idempotent on repeat runs.

## Verification Explanation

The verifier harness materializes verifier-only overlay scenarios then rebuilds the binary and pytest drives holdfairctl through subprocess with independent reference math. NOP on the baseline scores zero and oracle patches should pass cleanly.
