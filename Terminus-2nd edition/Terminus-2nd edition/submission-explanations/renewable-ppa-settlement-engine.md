# Submission explanations - renewable-ppa-settlement-engine

**Task folder:** tasks/renewable-ppa-settlement-engine/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-10T09:58:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Coastal wind and solar operators must close a renewable PPA billing window from SCADA readings, strike tables, index curves, curtailment overlays, and ISO holiday calendars. Behavior is split across interval alignment, curtailment masking, strike versus index pricing, holiday day counts, and invoice rollup. Fixing one module often passes bundled scenarios while hidden traps on curtailment boundaries or exact market keys still fail. A decoy meter preview module sits off the settlement hot path. Independent settlement math across stages makes partial fixes look complete until edge fixtures run.

## Solution Explanation

The oracle applies five unified-diff patches to interval alignment, curtailment mask, market lookup, strike math, and holiday rollup modules, then rebuilds ppareconctl. The key insight is reading half-open curtailment rules, UTC floor alignment, max strike pricing, and holiday subtraction from the cited docs rather than tweaking one obvious file. Patches stay small and module-local so export rollup reads corrected staging lines.

## Verification Explanation

test.sh rebuilds ppareconctl before pytest. Tests invoke the CLI via subprocess and compare JSONL, SQLite, and invoice output to ppa_settlement_math expectations. Bundled scenarios cover clean intervals, curtailment, strike floor, holidays, and multi-meter rows. Hidden fixtures under /opt/verifier-fixtures exercise curtailment end boundaries and exact market interval lookup.
