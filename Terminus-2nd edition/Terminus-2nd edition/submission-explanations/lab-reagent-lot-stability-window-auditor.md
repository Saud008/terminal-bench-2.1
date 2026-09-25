# Submission explanations — lab-reagent-lot-stability-window-auditor

**Task folder:** tasks/lab-reagent-lot-stability-window-auditor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a two-stage reagentwin closure workflow where correlate fuses lot certificate hashes, thermal excursion peaks, assay coupling, and calendar extension into one artifact, then publish-closure ranks rows from that artifact alone. Six interacting defects span generation monotonicity, digest field order, case folding, inclusive minute boundaries, cumulative expiry days, and severity-first rank ladder. Fixing one module leaves partial closure reports that pass some bundled cases but fail hidden verifier fixture traps or cross-run generation checks.

## Solution Explanation

The oracle applies six unified diffs under correlation_store, provenance_digest, assay_coupling, chrono_integral, calendar_extend, and closure_rank, then rebuilds reagentwin. correlate_generation increments on every correlate call, digests use lot_id:as_of_date:assay_code, aliases compare case-insensitively, excursion uses greater-or-equal on minute_index, expiry adds both day counters, and closure rows sort by descending severity. publish-closure reads only the correlated artifact path documented in stability-closure-atlas.md.

## Verification Explanation

Pytest rebuilds reagentwin from live sources, invokes correlate and publish-closure through subprocess on every test, and compares closure JSON to an independent Python reference in reagentwin_validate.py. Bundled session bundles exercise boundary and rank-ladder cases while hidden bundles under verifier fixture directories probe alias poisoning and deep excursion spikes through fixture directory overrides. Cross-run tests assert correlate_generation persistence via reset-workspace.sh between sessions.
