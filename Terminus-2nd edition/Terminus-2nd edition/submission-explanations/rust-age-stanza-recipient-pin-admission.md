# Submission explanations - rust-age-stanza-recipient-pin-admission

**Task folder:** tasks/rust-age-stanza-recipient-pin-admission/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T12:38:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation


This task is an offline age recipient-stanza admission governor. I rated it hard because admit/deny depends on several interacting contracts (fingerprint preimage, allow-list, quorum, overflow, witness ordering, ledger totals) spread across parse/policy/admit/seal modules. Fixing one module often makes the default corpus look fine while hidden corpus, env override, or malformed/overflow probes still fail. With about 19 checks, partial fixes rarely clear the full suite.

## Solution Explanation


The oracle installs corrected sources for header parse, fingerprint, allow-list, quorum, corpus walk, decision, witness staging, and ledger export. It then rebuilds agerecv and runs stage-witness plus seal-ledger against the fixture policy. Fingerprints must use the documented uppercase TYPE plus newline-joined args, and the allow-list is a positive match rather than an inverted deny list. Quorum counts distinct matched pins, overflow uses a strict greater-than max_recipients check, and the sealed ledger drops decoy fields while keeping sorted reasons and accurate malformed totals. Re-running seal on an unchanged witness must rewrite byte-identical ledger JSON.

## Verification Explanation


test.sh rebuilds agerecv each run. Pytest (19 tests) drives the binary via subprocess against fixtures and /opt/verifier-fixtures/age_hidden. The test module recomputes reference fingerprints and decisions independently, so hardcoded golden JSON fails. Staging snapshot shape, export idempotency, decoy absence, and AGE_CORPUS_DIR override are graded explicitly. NOP on the broken image scores 0. after oracle patches the suite passes.
