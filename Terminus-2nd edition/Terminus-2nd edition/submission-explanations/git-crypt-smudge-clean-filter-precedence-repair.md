# Submission explanations — git-crypt-smudge-clean-filter-precedence-repair

**Task folder:** tasks/git-crypt-smudge-clean-filter-precedence-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because five cooperating Bash libraries must implement git-crypt-style clean, smudge, and export-manifest behavior under six /app/docs contracts at once. Agents often encrypt before checking .gitattributes, which breaks pass-through paths like public/readme.txt and negated rules such as notes.txt or secret/public.txt in seeded repos. Smudge must verify HMAC only after CRLF-to-LF normalization, resolve keys from the --repo root even when cwd sits inside a submodule, and roll back /app/state/staging on decrypt failure without leaving partial files. Export-manifest must apply the same attribute specificity as the filters rather than naively globbing every file under secret/. Partial fixes may roundtrip bundled plaintext while still failing submodule feedface key ids, corrupt HMAC exit code 2, or listing negated paths in the manifest JSON.

## Solution Explanation

The oracle replaces gc_attrs.sh, gc_keys.sh, gc_crypto.sh, gc_staging.sh, and gc_manifest.sh under /app/lib/ with golden implementations that follow filter-pipeline.md and gitattributes-rules.md. Clean resolves the winning filter attribute first, passes through non-gcrypt paths unchanged, and only then encrypts with repo-local key material and GCRYPT1 blob layout from crypto-hmac.md. Smudge pass-throughs plaintext blobs, rejects encrypted blobs on non-gcrypt paths with exit 2, normalizes line endings before HMAC verification, and atomically writes successful --staging output while deleting staging artifacts on failure. Export-manifest walks the fixture catalog with identical precedence scoring and writes /app/output/encrypted-manifest.json omitting negated and public paths. Submodule worktrees use .gcrypt/keys/default from the declared --repo directory regardless of process cwd.

## Verification Explanation

Twenty pytest functions drive /app/bin/gcrypt-filter clean, smudge, and export-manifest through subprocess on every run after reset-state.sh clears /app/state and /app/output. An independent reference_gcrypt module implements attribute scoring, encryption, decryption, and manifest generation so answers cannot be hard-coded from bundled blobs alone. Bundled base and submod-child repos cover pass-through clean, *.key filters, CRLF roundtrips, subdirectory smudge cwd, staging success and rollback, and manifest omission of negated entries. Hidden anti-cheat coverage generates seed-specific repos via gen_repo_fixture.sh, roundtrips non-catalog plaintext, and exercises a TB3_REPO_ROOT tree with distinct key material. CLI guard tests assert exit 1 for missing --repo or empty --path before any crypto runs.
