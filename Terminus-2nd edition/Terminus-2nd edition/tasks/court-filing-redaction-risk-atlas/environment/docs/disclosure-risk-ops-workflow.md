# Sealed-disclosure security ops workflow

This task is a **security** host-local sealed-record disclosure control plane. Court records officers admit filing bundles under redaction policy, expand party-alias reachability, scan for sealed-term and exhibit leakage with page-line anchors, then seal a digest-bound redaction-risk atlas for clerk triage. The working baseline under /app must keep alias closure, sealed-term gates, citation provenance, and atlas attestation aligned; it is not a generic service repair exercise.

## Operator pass

1. `filingatlas load-bundle` admits scenario inputs and writes `/app/state/bundle-fingerprint.json`.
2. `filingatlas index-parties` expands alias reachability into `/app/state/party-graph.json` and advances `index_revision`.
3. `filingatlas scan-risks` materializes exposure findings into `/app/state/risk-findings.json`.
4. `filingatlas emit-atlas` publishes `/app/output/redaction-risk-atlas.json` only when `index_revision > 0`.

Verb flags and paths: `/app/docs/cli-surface.md`.

## Local rebuild / reset (operators)

After Go source edits, rebuild with `/app/scripts/verifier-rebuild.sh`. Clear staged state with `/app/scripts/reset-state.sh` before cross-run checks.

## Fixture roots

Bundled scenarios: `/app/fixtures/scenarios/`. Hidden probes may appear under `/opt/verifier-fixtures/filingatlas`. Optional env `TB3_FIXTURE_DIR` overrides the fixture root; `TB3_SEALED_BIAS` may adjust sealed-term sensitivity on verifier-only scenarios.
