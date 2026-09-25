# Submission explanations - rail-signal-possession-conflict-ledger

**Task folder:** tasks/rail-signal-possession-conflict-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-27T20:45:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `games` (yard-block possession conflict playtest / sealed conflict-ledger win-condition export). Choose **Game** on the platform form. Do not set `debugging`, `software-engineering`, `data-processing`, or `security` (project/classifier blocked). Do not set `data-administration` (not in Harbor schema). Prior uploads failed classifier on those labels; keep the playtest/win-condition framing and the explicit “not a Rust CLI / interlocking / debugging” negation. If games ever classifies as SE, fall back to system-administration host-local control-plane language.

## Difficulty Explanation

Hard because the sealed conflict playtest export must satisfy several interacting scoring rules at once,zone reachability,half-open windows,signal traps,override suppressions,salt order,and load sequencing,and a miss on one rule can still fail later emit checks.Held-out overlays plus a decoy helper that looks like the emit path make partial playtests fail even when bundled scenarios look fine.

## Solution Explanation

The oracle updates the trackgraph staging and conflict-emit modules under /app,rebuilds railpos,and re-runs compile then emit on the same fixtures.Key insight is emit must read the on-disk staged playfield snapshot and authority ticket and apply the doc rules for zone intersection and ordering when sealing ledger groups.

## Verification Explanation

test.sh rebuilds the binary then pytest drives railpos over subprocess.Expected ledgers are recomputed from fixtures so golden pastes fail,and some cases check staging bytes before export fields.NOP should score zero and the oracle path should pass.
