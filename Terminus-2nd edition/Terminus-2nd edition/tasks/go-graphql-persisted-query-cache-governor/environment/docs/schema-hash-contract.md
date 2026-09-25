# Schema hash contract

Tenant schema hashes live in FIXTURE_DIR/schemas.json under tenants.TENANT_ID.schema_hash.

During ingest each manifest schema_hash must equal the tenant schema hash from schemas.json.

## Compound schema mode

When TB3_COMPOUND_SCHEMA=1 the expected manifest schema_hash is:

cmp:TENANT_ID:BASE_SCHEMA_HASH

where BASE_SCHEMA_HASH is the schemas.json value for the tenant.

Compound mode applies to ingest validation and the schema_hash field written into pq-staging.json.

Manifest manifest_version must be 1. Schema compatibility is determined solely by schema_hash equality against the expected tenant schema (or compound form), not by manifest_version numeric equality alone.
