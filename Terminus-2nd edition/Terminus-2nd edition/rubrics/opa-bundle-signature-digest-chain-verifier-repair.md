# Platform rubric — opa-bundle-signature-digest-chain-verifier-repair

**Task folder:** tasks/opa-bundle-signature-digest-chain-verifier-repair/
**Written:** 2026-06-26T06:00:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent canonicalizes manifest member paths with POSIX .. collapse before digest math, +3
Agent rejects manifest paths that escape the bundle root such as ../../etc/passwd, +3
Agent writes /app/state/preview-ledger.json with lexicographic order before chain roots, +3
Agent computes full and scoped chain roots from preview ledger not manifest order, +3
Agent validates HMAC signatures with scope and chain_root from /app/trust/keys.json, +3
Agent rejects revoked key_id with revoked true and non-zero verify exit, +2
Agent captures every data and input binding in eval trace with seed substitution, +3
Agent persists eval audit binding count matching reference trace bindings, +1
Agent rebuilds bundlectl with go build before pytest in test harness, +1
Agent ignores decoy wrap.go manifest-order helper off verify hot path, +1
Agent fixes only digest.go leaving eval trace bindings incomplete, -3
Agent uses manifest declaration order for scoped signature chain roots, -3
Agent compares revoked fingerprint field instead of key_id, -2
Agent places Trace types in trace.go causing partial stub build failure, -2
Agent skips data.foo binding while eval allow appears correct, -2
