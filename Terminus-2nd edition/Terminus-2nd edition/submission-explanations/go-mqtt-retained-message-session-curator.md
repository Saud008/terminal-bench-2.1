# Submission explanations - go-mqtt-retained-message-session-curator

**Task folder:** tasks/go-mqtt-retained-message-session-curator/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T16:00:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is an offline MQTT session curator: mqttsessctl must stage tamper-evident broker journals, reconstruct wildcard matching, retained stores, QoS inflight tables, and session expiry, then publish atlas and delivery ledger exports with no live broker. I rated it hard because the behavior is split across wildcard-match-contract.md, retained-store-contract.md, qos-inflight-contract.md, session-expiry-contract.md and topicmatch, retainstore, qosledger, sessionexp, atlasemit. Fixing one layer often looks fine on bundled journals while other checks still fail. The painful parts are emit-atlas must trust the on-disk staging snapshot and positive curator_seal, not re-derive everything from raw fixtures, and there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 20 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (wildcard.go, retained.go, inflight.go, expiry.go, export.go) into /app via apply_frontier.sh, patches IncrementCuratorSeal in reconcile.go, rebuilds the project, and exercises /app/bin/mqttsessctl against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot, and only then should merge advance the seal and export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (20 tests) calls /app/bin/mqttsessctl via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot digest before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
