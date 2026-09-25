# Intake vault schema

calbind ingest writes /app/state/intake-vault.json as a map keyed by batch id.

Each batch entry contains:

- batch_id
- pack
- as_of_date
- instrument: staged instrument object with cert_valid, cert_digest, std_root, combined_uncertainty, expanded_uncertainty, authorized_tech, decisions, out_of_tolerance_count

Ingest overwrites the batch entry on each call. Fuse reads this vault and does not reload pack JSON during export.
