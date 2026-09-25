# Import preview and contract acceptance

This document is the **contract acceptance** checklist for `bundlectl`. Supporting protocol detail lives in `/app/docs/bundle-contract.md`, `/app/docs/eval-trace-schema.md`, and `/app/docs/fixture-catalog.md`.

## Import-preview (member paths)

Before digest or scoped-signature math, **import-preview** each manifest member path into its canonical slash form:

1. Replace backslashes with `/`.
2. Strip a leading `./`.
3. Collapse `/./` and resolve `..` segments (POSIX-style).
4. Reject paths that escape the bundle root after preview.

Sort previewed member paths by **UTF-8 lexicographic order** for the full-bundle digest chain. `MANIFEST.json` declaration order is not digest order.

Persist the preview snapshot to `/app/state/preview-ledger.json` before digest math. Digest iteration must follow the ledger `order` field (see `/app/docs/preview-ledger-schema.md`). The legacy helper in `/app/internal/verify/legacy_manifest_chain.go` computes roots using manifest declaration order for diagnostics only. Contract acceptance never uses manifest order.

Rego module references use dotted import paths (`package policy`); bundle member paths use slashes (`policies/allow.rego`). Only on-disk member paths enter the digest chain. Manifest aliases such as `./data/../data/data.json` must preview to `data/data.json`.

## Contract acceptance — `bundlectl verify`

| Requirement | Acceptance |
|-------------|------------|
| Flags | `--bundle <dir>` only; **no** `--seed` |
| Path preview | Canonical member paths before hashing |
| Digest chain | Lexicographic member order; rolling SHA-256 per `/app/docs/bundle-contract.md` |
| Scoped signatures | Each `.signatures.json` entry's `chain_root` matches the scoped subset digest for its `scope` prefix |
| Signatures | HMAC-SHA256 over `scope \|\| chain_root` with `/app/trust/keys.json` material |
| Revoked keys | Non-zero exit; JSON includes `"revoked": true` when `key_id` is revoked |
| Success JSON | `"ok": true`, `"chain_root"`, `"digests"` map (canonical path → per-file SHA-256 hex) |
| Failure JSON | `"ok": false` with `"reason"` |

Verify hashes on-disk bytes only. Placeholders such as `__THRESHOLD__` in fixture input files are **not** substituted during verify.

## Contract acceptance — `bundlectl eval`

| Requirement | Acceptance |
|-------------|------------|
| Seed substitution | Apply to `--input` JSON bytes **before** parsing; replace `__THRESHOLD__` with decimal digits derived from `/app/internal/seed/seed.go` |
| Threshold type | After substitution, `input.threshold` is a JSON **string** (quoted digits), not a number |
| Evaluation | Package `policy`, rule `allow`, against bundle `data/data.json` |
| Trace bindings | Every `data.*` and `input.*` reference in the evaluated expression appears with substituted JSON values |
| Trace steps | Exactly `["load_data", "eval_expr", "decision"]` |
| Export | `--export` file contains the same JSON object as stdout |

Good bundles in `/app/fixtures/bundles/` (`allow-basic`, `deny-edge`, `multi-scope`, `path-normalize`) must pass verify and eval for every seed in `/app/fixtures/seeds.json`. Trap bundles (`tampered-member`, `revoked-signer`, `bad-scope-chain`, `path-escape`) must fail verify.
