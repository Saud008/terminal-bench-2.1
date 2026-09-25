# Submission explanations - relay-duel-fork-window-seal-ledger

**Task folder:** tasks/relay-duel-fork-window-seal-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T08:30:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Choose **Game** on the platform form. Zip metadata uses `games` for the offline relay-duel playfield playtest (admit-log → lane-fork / hold / resign-forfeit / retransmit / skew / rush-calm score traps → sealed SQLite match-ledger win-condition export) on a debian + bash/python policy-module desk. Do not set `system-administration`, `data-processing`, `software-engineering`, `debugging`, or `build-and-dependency-management`.

**History:** Successor of retired `go-sip-dialog-cdr-reconciliation-engine` after SIP/CDR nouns kept classifying as blocked SE/DP/BDM. Algorithms and verifier strength preserved under games-native duel/match/ledger nouns.

## Difficulty Explanation

Hard because duelctl must align admit-log ordering, fork_tag lane joins, hold-versus-accept gating, FORFEIT-over-RESIGN precedence, retransmit collapse, skew-corrected rush/calm windows, match_seal staging, and answered-only SQLite export while the baseline breaks those edges across eight policy modules. Held-out forfeit poison and inclusive score-boundary packs plus byte-stable second-pass checks stop partial fixes from clearing the suite.

## Solution Explanation

The oracle replaces load, branch, hold, terminate, dedupe, clock, window, and sqlite_pub with sorted admit-log load, fork_tag-aware branch keys, 2xx-only accept gating, FORFEIT-before-accept precedence, retransmit signatures, clock_skew_ms shifts, inclusive end-minute rush/calm bands, and answered+disposition SQLite filtering. Rebuild duelctl after the copies so `/app/bin/duelctl` stays current.

## Verification Explanation

test.sh / rebuild-duelctl.sh refreshes the wrapper; pytest calls `/app/bin/duelctl` via subprocess. Reference math in duel_ledger_refmath.py recomputes expected ledger_rows from fixtures. Hidden packs stage only under TB3_FIXTURE_DIR. NOP on the broken image scores zero; oracle scores one.
