# gcrypt-filter CLI

All paths below are relative to the repository root passed with --repo.

## clean

```
gcrypt-filter clean --repo ROOT --path RELPATH [--config /app/config/filter.json]
```

Reads plaintext bytes from stdin. Writes the git index blob to stdout.

Pipeline order is defined in /app/docs/filter-pipeline.md: attribute match must be evaluated before any encryption or pass-through decision.

Exit 0 on success. Exit 1 when the repo root is invalid or RELPATH is empty.

## smudge

```
gcrypt-filter smudge --repo ROOT --path RELPATH [--config PATH] [--staging]
```

Reads an index blob from stdin. Writes working-tree plaintext to stdout.

When --staging is set, also writes the decrypted plaintext to /app/state/staging/RELPATH after successful HMAC verification. On decrypt or HMAC failure, the staging file must not exist afterward.

## export-manifest

```
gcrypt-filter export-manifest --repo ROOT --output PATH [--config PATH]
```

Walks tracked fixture files under the repo (see /app/docs/fixture-catalog.md) and writes JSON per /app/docs/export-manifest-schema.md. Only paths whose winning gitattributes rule sets filter=gcrypt are listed.

Exit 0 on success. Exit 1 when ROOT is invalid.
