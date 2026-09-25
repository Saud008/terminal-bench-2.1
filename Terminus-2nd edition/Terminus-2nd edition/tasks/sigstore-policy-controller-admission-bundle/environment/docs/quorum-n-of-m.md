# Quorum attestation admission

## Evaluation precedence (terminal)

For each pull request, stop at the first terminal decision:

1. **digest_deny** — normalized image digest matches any merged digest-deny pin (exact digest match after normalization). Cannot be overridden.
2. **revocation_hit** — see revocation-seal.md.
3. Let **matched** be envelopes whose normalized `subject_digest` equals the normalized image digest.
4. Let **trusted** be matched envelopes that trust-bind (see trust-bind-policy.md).
5. **trust_unbind** — if trusted is empty → deny.
6. Let **pred_ok** be trusted envelopes that pass the predicate allowlist.
7. **predicate_reject** — if pred_ok is empty → deny.
8. **builder_deny** — if any pred_ok envelope matches a builder deny glob → deny.
9. **builder_require_miss** — if require list is non-empty and no pred_ok envelope matches a require glob → deny.
10. Collect **candidates**: pred_ok envelopes that do not match builder deny and (when require is non-empty) match at least one require glob.
11. **quorum_fail** — count of **distinct** `envelope_id` values among candidates is less than configured `quorum_k` → deny.
12. **admit_verified** — allow; record contributing envelope_ids sorted lexicographically.

## Policy pack selection (seed)

Let `digest` be the 32-byte SHA-256 of the UTF-8 seed string.

### Subset

- Include pack at config index `i` when `(digest[5 + (i % 10)] % 2) == 1`.
- If none selected, include exactly `packs[digest[7] % len(packs)]`.

### Shuffle

Copy selected names to `out`. For `i` from `len(out)-1` down to `1`:

- `j = digest[(i * 5 + 3) % len(digest)] % (i + 1)`
- swap `out[i]`, `out[j]`

Merge packs in final `out` order. Digest-deny pins **union**. Predicate allows **union**. Builder deny **union**. Builder require **replace** when later pack require is non-empty. Revocations **union**.

Exported `policy_packs` on the witness and report must list the same selected names in the same shuffled order.
