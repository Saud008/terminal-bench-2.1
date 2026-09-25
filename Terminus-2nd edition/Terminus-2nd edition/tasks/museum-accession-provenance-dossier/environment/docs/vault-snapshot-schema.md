# Vault snapshot schema

On this games museum accession playtest, musdoss vault load writes /app/state/accession-vault.json with:

- archive_seq: monotonic counter incremented on every successful archive load for the same snapshot path, regardless of seed or archive
- seed, archive, focus_accession_id, museum_id, as_of_date
- objects: scoped accession records
- transfers, loans, restorations, rights: scoped rows tied to accession_id

Accession ids are seed-scoped from raw accession_id or ref per catalog load rules.

The archive file's archive_name must exactly match the --archive name used to select
it. A load must reject a mismatched name without replacing the existing snapshot or
advancing archive_seq. If an existing snapshot cannot be decoded, loading must fail
rather than silently reset its archive_seq.
