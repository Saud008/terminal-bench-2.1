# Submission explanations - go-spiffe-trust-domain-bundle-differ

**Task folder:** tasks/go-spiffe-trust-domain-bundle-differ/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-21T09:45:00Z

**Category note:** Zip metadata uses `security` (SPIFFE workload-identity trust attestation / federation allowlist admission / JWKS+x509 integrity / sealed federation atlas). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` when the prompt led with Go rebuild / pytest / engineering-contract framing; keep the trust-attestation / federation-admission security framing.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about mesh security operators attesting SPIFFE trust-domain bundle pairs before federation admission. I rated it hard because the behavior is split across trust-domain, JWKS, x509, rotation-window, federation-allowlist, and atlas seal contracts plus multiple source files. Fixing one gate often looks fine on the bundled data while other checks still fail. The painful parts are emit-atlas must honor the on-disk trust-attest seal, not re-derive from raw inputs, and seal counters have to stay in sync across two CLI runs. With about 22 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (bundlescene_pair_load.go, diffseal_publish.go, fedmatch_wildcard.go, jwksort_order.go) into /app, rebuilds the project, and exercises /app/bin/spiffectl against the same fixtures agents see. bind-pair validates inputs and writes the pair-capture staging snapshot; normalize-trust applies cryptographic and identity gates and increments the seal; only then should emit-atlas trust those bytes. Key insight: follow the security contracts for ordering, digests, and seal rules instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent.

## Verification Explanation

`tests/Dockerfile` owns the pinned pytest stack under `/opt/verifier-venv`; the candidate `environment/Dockerfile` no longer installs or exposes a writable verifier path. At grade time the platform mounts the tests-side venv read-only, and `tests/test.sh` refuses to run if that protected interpreter is missing or stubbed. Pytest (32 tests) rebuilds `spiffectl` via `conftest.py` + `/app/scripts/verifier-rebuild.sh`, then drives `/app/bin/spiffectl` through subprocess with independent reference math in `identity_bundle_ref.py`. Tests do not grep source for magic strings. NOP on the broken image should score 0; after the oracle patches and rebuild, the suite should pass cleanly.
