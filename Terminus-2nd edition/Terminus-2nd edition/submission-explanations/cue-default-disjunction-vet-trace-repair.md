# Submission explanations — cue-default-disjunction-vet-trace-repair

**Task folder:** tasks/cue-default-disjunction-vet-trace-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a multi-stage cuectl pipeline where stage 1 composes eval snapshots, a guard validates invariants, and stage 2 vet and export read only the on-disk snapshot. Disjunct defaults, closed schema rejection, embed cycle detection, and lineage formatting interact across several cuewrap modules. Fixing one module often passes bundled workspaces while hidden twin fixtures, snapshot rebinding, or export-only paths still fail. Partial compose fixes can leave stale snapshot bytes that stage 2 trusts incorrectly.

## Solution Explanation

The oracle installs corrected cuewrap sources, rebuilds cuectl, and runs the same CLI paths agents use. Compose must detect cycles and closed violations before writing snapshots, apply seed-based disjunct defaults once, and pass guard checks. Vet and export then assemble JSON from snapshot values without re-evaluating configs. Snapshot bind logic must discard tampered files and recompose when headers or values drift.

## Verification Explanation

test.sh rebuilds cuectl before pytest. Tests invoke cuectl vet and export via subprocess and compare JSON to an independent reference implementation in the verifier library. Hidden workspaces under verifier fixtures exercise disjunct and provenance behavior outside the bundled catalog. Partial golden module swaps verify that decoy formatters alone cannot satisfy vet contracts. NOP on the broken baseline should score zero while the oracle passes the full suite.
