Implement the ClusterImagePolicy quorum admission workflow for slsacip at /usr/local/bin/slsacip. The working CLI must bind Fulcio roots to Cosign envelopes under digest-deny pins, half-open revocation windows, exact predicate allowlists, builder globs, and quorum_k, stage /app/state/slsacip/trust-witness.json, and seal /app/output/slsa-admission-ledger.json (or --output).

Contracts: /app/docs/fulcio-root-bind.md, /app/docs/digest-pin-deny.md, /app/docs/revoke-halfopen.md, /app/docs/predicate-exact-allow.md, /app/docs/builder-glob-authz.md, /app/docs/quorum-n-of-m.md, /app/docs/trust-witness-format.md, /app/docs/ledger-seal-format.md. Config: /app/config/slsacip.json.

Do not edit /app/docs/, /app/fixtures/, /app/config/slsacip.json, or /tests/. Editable packages under /app/cipkernel/ must keep exported method sets stable.
