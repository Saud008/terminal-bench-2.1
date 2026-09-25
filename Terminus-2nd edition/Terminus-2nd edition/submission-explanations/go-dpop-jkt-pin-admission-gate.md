# Submission explanations - go-dpop-jkt-pin-admission-gate

**Task folder:** tasks/go-dpop-jkt-pin-admission-gate/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T15:40:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is an offline DPoP proof-of-possession gate with HTTP open/check/commit. I rated it hard because jkt thumbprints, htm/htu binding, bidirectional iat skew, and jti nonce replay must all agree with the staged chainhead before the deny ledger can seal correctly. Fixing one package often clears sample fixtures while pin-registry overrides or replay windows still fail. With roughly thirty checks, partial patches rarely survive the full suite.

## Solution Explanation

The oracle installs corrected sources for proof verification, jkt pin registry lookup, jti nonce ledger membership, chainhead staging order, and deny-ledger seal emit. It rebuilds jktadmit and exercises the session-open then proof-check then audit-commit HTTP cycle against the fixture policy. The critical detail is that jkt must be the SHA-256 JWK thumbprint established at open, htm compares case-insensitively, and commit must mirror staged deny totals without decoy telemetry fields. Replay checks must consult the ledger before recording a new jti, and JKTADMIT_PIN_DIR must redirect the pin registry path when set.

## Verification Explanation

test.sh rebuilds jktadmit each run. Pytest drives the HTTP surface via subprocess and compares responses plus on-disk chainhead and deny-ledger artifacts to an independent reference module. Tests do not grep source for magic strings. Pin-registry overrides and documented verifier fixture paths are graded explicitly. NOP on the broken image scores 0; after oracle patches the suite passes.
