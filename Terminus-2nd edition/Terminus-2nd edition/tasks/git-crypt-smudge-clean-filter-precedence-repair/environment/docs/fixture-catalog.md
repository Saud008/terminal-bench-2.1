# Fixture catalog

## Bundled repos under /app/fixtures/repos/

| Name | Purpose |
|------|---------|
| base | Mixed plaintext, secret/** glob, *.key pattern, negated public file |
| submod-child | Submodule-shaped root with its own key id |

Tracked files for export-manifest (relative to each repo root):

### base

- secret/plain.txt
- secret/nested/data.bin
- public/readme.txt
- vault/config.key
- notes.txt

### submod-child

- secret/inner.txt
- public/note.txt
- overlay.key

## Generated repos

/app/scripts/gen_repo_fixture.sh --seed SEED --output ROOT creates a verifier-only tree with nested attribute overrides. Seed repos include at least one path where a broad secret/** rule is negated for a single nested file.

## TB3 verifier-only repo

When tests/test.sh sets TB3_REPO_ROOT (default /opt/verifier-fixtures/tb3-repo), the verifier uses that hidden tree for secret/hidden.bin roundtrip checks. The tree is not copied under /app.
