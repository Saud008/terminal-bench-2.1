# Submission explanations - go-openapi-parameter-style-form-explode-binding

**Task folder:** tasks/go-openapi-parameter-style-form-explode-binding/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-27T00:00:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `security` (API-edge parameter trust-policy admission / style-explode authenticity gates / required-field trust blocks / tamper-evident witness staging / sealed bind-snapshot attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form.

## Difficulty Explanation

This task is about API-edge security operators deploying paramgate as a parameter trust-policy admission gate at /usr/local/bin/paramgate. I rated it hard because behavior is split across ingest binding, explode defaults, canonical ordering, staging, and export publishing in separate modules (`query.go`, `explode_policy.go`, `canonical.go`, `binder.go`, `staging.go`, `publish.go`). Fixing query parsing alone passes bundled style cases but still fails witness export, canonical nested order, or hidden TB3 probes. Partial fixes to `emit.go` without `publish.go`, or staging raw parser maps without canonicalization, look plausible but fail cross-stage tests. Legacy `wrap.go` distractors and multi-doc contracts increase the search space.

## Solution Explanation

The oracle installs corrected sources into `/app/internal/bind/`, rebuilds paramgate, and exercises the same HTTP fixtures agents see. Ingest binds and canonicalizes parameters, writes the witness snapshot with monotonic `bind_seq`, and export publishing reads snapshot params (not transient maps). Style/explode defaults live in `explode_policy.go`; comma arrays, bracket objects, form meta pairs, UTC dates, latin1 JSON, and admin fragment routes must all align with the doc contracts.

## Verification Explanation

test.sh bootstraps reward/CTRF early, rebuilds the binary, then runs pytest (22 tests) against the live HTTP server. Tests recompute expected params from fixtures via an independent reference module; hidden TB3 cases under `/opt/verifier-fixtures/` exercise canonical order and form-object encoding paths the bundled probes do not fully cover. NOP on the broken image scores 0. Oracle after patching and rebuild scores 1.0.
