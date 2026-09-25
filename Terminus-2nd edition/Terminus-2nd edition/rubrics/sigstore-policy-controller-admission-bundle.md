# Platform rubric — sigstore-policy-controller-admission-bundle

**Task folder:** tasks/sigstore-policy-controller-admission-bundle/
**Written:** 2026-07-19T18:40:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent stages /app/state/slsacip/trust-witness.json after cip-tier merge, +3
Agent seals /app/output/slsa-admission-ledger.json with audit_digest including revoke_fingerprint, +3
Agent applies digest_deny before trust bind per quorum-n-of-m.md, +3
Agent matches Fulcio issuer/subject with full-string anchored globs, +3
Agent enforces half-open revocation windows [start, end), +3
Agent requires exact predicate allowlist equality (no substring), +2
Agent counts distinct envelope_id values for quorum_k, +2
Agent rebuilds slsacip with go build after editing cipkernel packages, +2
Agent leaves /app/docs, fixtures, and config/slsacip.json unchanged, +1
Agent patches only rootbind while pindeny and sealhex stay wrong, -3
Agent omits revoke_fingerprint from audit_digest payload, -3
Agent edits protected fixtures or verifier math under /tests to force a pass, -5
