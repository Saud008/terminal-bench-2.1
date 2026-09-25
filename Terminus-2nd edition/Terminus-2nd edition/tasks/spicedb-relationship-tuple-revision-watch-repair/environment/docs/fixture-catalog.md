# Fixture catalog

Fixtures live under /app/fixtures.

## catalog.json

Lists named fixture bundles for POST /v1/admin/seed.

## tuples/base.json

Seed operations:

- doc plan viewer via group:eng#member
- doc group:eng member user:alice
- doc plan viewer user:bob with caveat allow_subject user:bob
- audit trail reader user:carol

After seed, revision-snapshot.json is written at the final revision.

## Usage

POST /v1/admin/seed with body {"fixture":"tuples/base"} loads the bundle.

Relative fixture names omit the .json suffix.

## Namespace prefix delete testing

Use POST /v1/admin/delete-namespace-prefix with {"prefix":"doc"} to tombstone all doc namespaces. Live permission checks after prefix delete must reflect tombstoned tuples per /app/docs/check-contract.md.
